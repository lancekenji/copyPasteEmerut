from django.shortcuts import render,redirect,reverse
from . import forms,models
import xlwt
import xlrd
import os
from django.conf import settings as django_settings
from Utils import queryset_to_workbook
from datetime import datetime,time
from django.db.models import Sum,Q,Count
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import auth
from django.conf import settings
from datetime import date, timedelta
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings
from donor import models as dmodels
from patient import models as pmodels
from donor import forms as dforms
from patient import forms as pforms
import logging
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.http import JsonResponse

#The mail addresses and password
sender_address = 'redcross.help.portal@gmail.com'
sender_pass = 'ljnanvxmokehqfjs'

def pdf_view(request):
    if request.method == 'POST':
        if request.POST.get('report_Type') == 'DonorList':
            donors=dmodels.Donor.objects.all().select_related('user')
            return render(request, 'blood/donor_template.html', {'donors': donors})
        elif request.POST.get('report_Type') == 'BloodDonation':
            donations=dmodels.BloodDonate.objects.all().select_related('donor')
            return render(request, 'blood/donation_template.html', {'donations': donations})
        elif request.POST.get('report_Type') == 'Transaction':
            blood_requests = models.BloodRequest.objects.all()
            print(blood_requests)
            return render(request, 'blood/transaction_template.html', {'blood_requests': blood_requests})
        elif request.POST.get('report_Type') == 'BloodStocks':
            pass
        else:
            pass
            
def request_history_view(request):
    blood_requests = models.BloodRequest.objects.all()
    return render(request,'blood/request_history.html',{'blood_requests':blood_requests})

def home_view(request):
    x=models.Stock.objects.all()
    if len(x)==0:
        blood1=models.Stock()
        blood1.bloodgroup="A+"
        blood1.save()

        blood3=models.Stock()
        blood3.bloodgroup="B+"
        blood3.save()

        blood5=models.Stock()
        blood5.bloodgroup="AB+"
        blood5.save()

        blood7=models.Stock()
        blood7.bloodgroup="O+"
        blood7.save()

    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    announcements = models.Announcement.objects.all().order_by('-id')[:5]
    make_request = False

    if 'make_request' in request.session:
        print("the make request " + str(request.session['make_request']))
        make_request = request.session['make_request']
        del request.session['make_request']
    return render(request,'blood/index.html',{"announcement":announcements,"make_request":make_request})

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

def set_blood_group(request, pk, pk1):
    donor = dmodels.Donor.objects.get(id=pk)
    bloodDonate = dmodels.BloodDonate.objects.get(donor_id=pk, id=pk1)
    if request.method == 'POST':
        request_form = dforms.BloodGroupForm(request.POST, instance=donor)
        if request_form.is_valid():
            print(request_form.cleaned_data)
            donor.bloodgroup = request_form.cleaned_data['bloodgroup']
            donor.save()
            bloodDonate.bloodgroup = request_form.cleaned_data['bloodgroup']
            print(bloodDonate.id)
            bloodDonate.save()
            return HttpResponseRedirect('/blood-test/'+str(bloodDonate.id))
        
    return HttpResponseRedirect('/blood-test/'+str(bloodDonate.id))

@login_required(login_url='adminlogin')
def fetchNotifications(request):
    notifications = models.AdminNotification.objects.filter(read=False).count()
    return JsonResponse({'count':notifications})

@login_required(login_url='adminlogin')
def getNotifications(request):
    models.AdminNotification.objects.filter().update(read=True)
    notifications = models.AdminNotification.objects.all().order_by('-created_at')
    return render(request, 'blood/notifications.html', {'notifications': notifications})

def upload_announcement(request):
    if request.method == 'POST':
        request_form = forms.AnnouncementForm(request.POST)
        if request_form.is_valid():
            print("redirec")
            announcement_request = request_form.save(commit=False)
            announcement_request.save()
            request.session['announcement_upload'] = True
            return HttpResponseRedirect('/admin-announcement')
        request.session['announcement_upload'] = False
        return HttpResponseRedirect('/admin-announcement')

    return render(request, 'blood/admin_announcement.html')

def delete_announcement(request,pk):
    announcement = models.Announcement.objects.get(id=pk)
    announcement.delete()
    request.session['announcement_delete'] = True
    return HttpResponseRedirect('/admin-announcement')
def update_announcement_view(request,pk):
    announcement = models.Announcement.objects.get(id=pk)
    announcement_form = forms.AnnouncementForm()
    mydict = {'announcement_form': announcement_form,'announcement':announcement}
    if request.method == 'POST':
        announcement_form = forms.AnnouncementForm(request.POST,instance=announcement)
        if announcement_form.is_valid():
            announcement_form.save()
            request.method = 'GET'
            request.session['announcement_save'] = True
            return HttpResponseRedirect('../admin-announcement')
        request.session['announcement_save'] = False
        return HttpResponseRedirect('admin-announcement')
    return render(request, 'blood/update_announcement.html', context=mydict)
def admin_announcement(request):
    announcement_save = False
    announcement_upload = False
    announcement_delete = False
    if 'announcement_save' in request.session:
        announcement_save = request.session['announcement_save']
        del request.session['announcement_save']
    if 'announcement_upload' in request.session:
        announcement_upload = request.session['announcement_upload']
        del request.session['announcement_upload']
    if 'announcement_delete' in request.session:
        announcement_delete = request.session['announcement_delete']
        del request.session['announcement_delete']
    announcements = models.Announcement.objects.all().order_by('-id')[:5]
    return render(request, 'blood/admin_announcement_list.html', {"announcements": announcements,'announcement_save':announcement_save,'announcement_upload':announcement_upload,'announcement_delete':announcement_delete})


def is_donor(user):
    return user.groups.filter(name='DONOR').exists()

def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


def afterlogin_view(request):
    if is_donor(request.user):
        return redirect('donor/donor-dashboard')

    elif is_patient(request.user):
        return redirect('patient/patient-dashboard')
    else:
        return redirect('admin-dashboard')

@login_required(login_url='adminlogin')
def admin_donor_signup(request):
    userForm=dforms.DonorUserForm()
    donorForm=dforms.DonorForm()
    mydict={'userForm':userForm,'donorForm':donorForm}
    if request.method=='POST':
        userForm=dforms.DonorUserForm(request.POST)
        donorForm=dforms.DonorForm(request.POST,request.FILES)
        if userForm.is_valid() and donorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            donor=donorForm.save(commit=False)
            donor.user=user
            donor.bloodgroup=donorForm.cleaned_data['bloodgroup']
            donor.save()
            my_donor_group = Group.objects.get_or_create(name='DONOR')
            my_donor_group[0].user_set.add(user)
        return HttpResponseRedirect('admin-donor')
    return render(request,'blood/admin_donor_signup.html',context=mydict)

@login_required(login_url='adminlogin')
def admin_statistics_view(request):
    totalunit=models.Stock.objects.aggregate(Sum('unit'))
    totalA1 = 0
    totalB1 = 0
    totalO1 = 0
    totalAB1 = 0

    totalDonors = dmodels.Donor.objects.all().count()
    consoleLog = ""
    for i in dmodels.Donor.objects.all():
        if i.get_blood_group == "A+":
            totalA1+=1
        if i.get_blood_group == "B+":
            totalB1+=1
        if i.get_blood_group == "O+":
            totalO1+=1
        if i.get_blood_group == "AB+":
            totalAB1+=1


    dict={
        'A1':models.Stock.objects.all().filter(bloodgroup="A+"),
        'B1':models.Stock.objects.all().filter(bloodgroup="B+"),
        'AB1':models.Stock.objects.all().filter(bloodgroup="AB+"),
        'O1':models.Stock.objects.all().filter(bloodgroup="O+"),
        'A1ratio': totalA1 / totalDonors * 100 if totalA1 else 0,
        'B1ratio': totalB1 / totalDonors * 100 if totalB1 else 0,
        'O1ratio': totalO1 / totalDonors * 100 if totalO1 else 0,
        'AB1ratio': totalAB1 / totalDonors * 100 if totalAB1 else 0,

        'totaldonors':dmodels.Donor.objects.all().count(),
        'totalbloodunit':totalunit['unit__sum'],
        'totalrequest':models.BloodRequest.objects.all().count(),
        'totalapprovedrequest':models.BloodRequest.objects.all().filter(status='Approved').count(),
        'consoleLog': consoleLog
    }
    return render(request,'blood/admin_statistics.html',context=dict)

def admin_dashboard_view(request):
    counts = models.BLA.objects.values('bloodStock').annotate(count=Count('id'))
    total_count = sum([c['count'] for c in counts])
    approvedBloodDonatesToday = len(dmodels.BloodDonate.objects.filter(date=datetime.today(),status="Approved"))
    pendingBloodDonatesToday = len(dmodels.BloodDonate.objects.filter(date=datetime.today(),status="Pending"))
    rejectedBloodDonatesToday = len(dmodels.BloodDonate.objects.filter(date=datetime.today(),status="Rejected"))
    approvedBloodRequestsToday = len(models.BloodRequest.objects.filter(date=datetime.today(), status="Approved"))
    pendingBloodRequestsToday = len(models.BloodRequest.objects.filter(date=datetime.today(), status="Pending"))
    rejectedBloodRequestsToday = len(models.BloodRequest.objects.filter(date=datetime.today(), status="Rejected"))
    columns = [
        "donor"
    ]
    dailyReport = xlwt.Workbook()
    reportFileName = datetime.now().strftime("%Y%m%d") + ".xls"
    dailyReportSheet = dailyReport.add_sheet("Daily Report",cell_overwrite_ok=True)
    HEADER_SYTLE = xlwt.easyxf('font:bold on')
    dailyReportSheet.col(0).width = 7000
    dailyReportSheet.col(1).width = 7000
    dailyReportSheet.col(2).width = 7500
    dailyReportSheet.col(3).width = 7000
    dailyReportSheet.col(4).width = 7000
    dailyReportSheet.col(5).width = 7000
    #dailyReportSheet.write(0,0,"Approved Blood Donates",HEADER_SYTLE)
    dailyReportSheet.write(0,0,"Blood Requests",HEADER_SYTLE)
    dailyReportSheet.write(1,0,"Date",HEADER_SYTLE)
    dailyReportSheet.write(1,1,"Name",HEADER_SYTLE)
    dailyReportSheet.write(1,2,"Reason",HEADER_SYTLE)
    dailyReportSheet.write(1,3,"Type of Request Blood",HEADER_SYTLE)
    dailyReportSheet.write(1,4,"Unit",HEADER_SYTLE)
    dailyReportSheet.write(1,5,"Status",HEADER_SYTLE)
    blood_request_line = 2
    for blood_request in models.BloodRequest.objects.filter(Q(date=datetime.today()) & (Q(status="Rejected") | Q(status="Approved")) ):
        dailyReportSheet.write(blood_request_line, 0, blood_request.date.strftime("%m/%d/%y"))
        dailyReportSheet.write(blood_request_line, 1, blood_request.patient_name)
        dailyReportSheet.write(blood_request_line, 2, blood_request.reason)
        dailyReportSheet.write(blood_request_line, 3, blood_request.bloodgroup)
        dailyReportSheet.write(blood_request_line, 4, str(blood_request.unit) + "ml")
        dailyReportSheet.write(blood_request_line, 5, blood_request.status)
        blood_request_line+=1
    dailyReportSheet.write(blood_request_line, 0, "Blood Requests", HEADER_SYTLE)
    blood_request_line+=1
    dailyReportSheet.write(blood_request_line, 0, "Date", HEADER_SYTLE)
    dailyReportSheet.write(blood_request_line, 1, "Name", HEADER_SYTLE)
    dailyReportSheet.write(blood_request_line, 2, "Blood Type", HEADER_SYTLE)
    dailyReportSheet.write(blood_request_line, 3, "Unit", HEADER_SYTLE)
    dailyReportSheet.write(blood_request_line, 4, "Status", HEADER_SYTLE)
    blood_request_line+=1
    for blood_donate in dmodels.BloodDonate.objects.filter(Q(date=datetime.today()) & (Q(status="Rejected") | Q(status="Approved")) ):
        dailyReportSheet.write(blood_request_line, 0, blood_donate.date.strftime("%m/%d/%y"))
        dailyReportSheet.write(blood_request_line, 1, blood_donate.donor.user.first_name + " " + blood_donate.donor.user.first_name)
        dailyReportSheet.write(blood_request_line, 2, blood_donate.bloodgroup)
        dailyReportSheet.write(blood_request_line, 3, str(blood_donate.unit) + "ml")
        dailyReportSheet.write(blood_request_line, 4, blood_donate.status)
        blood_request_line+=1
    reportPath = "./static/reports/" + reportFileName
    dailyReport.save(reportPath)

    totalA1 = 0
    totalB1 = 0
    totalO1 = 0
    totalAB1 = 0

    total1 = 0
    total2 = 0
    total3 = 0
    total4 = 0

    current_year = date.today().year

    totalDonors = dmodels.Donor.objects.all().count()
    consoleLog = ""
    for i in dmodels.Donor.objects.all():
        if i.get_blood_group == "A+":
            totalA1+=1
        if i.get_blood_group == "B+":
            totalB1+=1
        if i.get_blood_group == "O+":
            totalO1+=1
        if i.get_blood_group == "AB+":
            totalAB1+=1
    for j in dmodels.Donor.objects.all():
        if j.age >= 20 and j.age <= 25:
            total1 += 1
        if j.age >= 26 and j.age <= 30:
            total2 += 1
        if j.age >= 31 and j.age <= 35:
            total3 += 1
        if j.age >= 36 and j.age <= 40:
            total4 += 1

    dict={
        'reportFileName':reportFileName,
        'approvedBloodDonatesToday':approvedBloodDonatesToday,
        'pendingBloodDonatesToday':pendingBloodDonatesToday,
        'rejectedBloodDonatesToday':rejectedBloodDonatesToday,
        'approvedBloodRequestsToday': approvedBloodRequestsToday,
        'pendingBloodRequestsToday': pendingBloodRequestsToday,
        'rejectedBloodRequestsToday': rejectedBloodRequestsToday,
        'A1':models.BLA.objects.filter(bloodStock__bloodgroup="A+"),
        'B1':models.BLA.objects.filter(bloodStock__bloodgroup="B+"),
        'AB1':models.BLA.objects.filter(bloodStock__bloodgroup="AB+"),
        'O1':models.BLA.objects.filter(bloodStock__bloodgroup="O+"),
        'totaldonors':dmodels.Donor.objects.all().count(),
        'totalbloodunit':total_count,
        'totalrequest':models.BloodRequest.objects.all().count(),
        'totalapprovedrequest':models.BloodRequest.objects.all().filter(status='Approved').count(),
        'consoleLog': consoleLog,
        'A1ratio': totalA1 / totalDonors * 100 if totalA1 else 0,
        'B1ratio': totalB1 / totalDonors * 100 if totalB1 else 0,
        'O1ratio': totalO1 / totalDonors * 100 if totalO1 else 0,
        'AB1ratio': totalAB1 / totalDonors * 100 if totalAB1 else 0,
        'total1':total1,
        'total2':total2,
        'total3':total3,
        'total4':total4,
        'jan_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=1).count(),
        'feb_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=2).count(),
        'mar_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=3).count(),
        'apr_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=4).count(),
        'may_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=5).count(),
        'jun_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=6).count(),
        'jul_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=7).count(),
        'aug_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=8).count(),
        'sep_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=9).count(),
        'oct_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=10).count(),
        'nov_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=11).count(),
        'dec_approved': dmodels.BloodDonate.objects.filter(status="Approved", date__year=current_year, date__month=12).count(),
        'jan_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=1).count(),
        'feb_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=2).count(),
        'mar_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=3).count(),
        'apr_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=4).count(),
        'may_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=5).count(),
        'jun_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=6).count(),
        'jul_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=7).count(),
        'aug_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=8).count(),
        'sep_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=9).count(),
        'oct_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=10).count(),
        'nov_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=11).count(),
        'dec_rejected': dmodels.BloodDonate.objects.filter(status="Rejected", date__year=current_year, date__month=12).count()
    }
    
    return render(request,'blood/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_blood_view(request):
    dict={
        'A1':models.BLA.objects.all().filter(bloodStock__bloodgroup="A+"),
        'B1':models.BLA.objects.all().filter(bloodStock__bloodgroup="B+"),
        'AB1':models.BLA.objects.all().filter(bloodStock__bloodgroup="AB+"),
        'O1':models.BLA.objects.all().filter(bloodStock__bloodgroup="O+"),

        'A1_PLA':models.PLA.objects.all().filter(bloodStock__bloodgroup="A+"),
        'B1_PLA':models.PLA.objects.all().filter(bloodStock__bloodgroup="B+"),
        'AB1_PLA':models.PLA.objects.all().filter(bloodStock__bloodgroup="AB+"),
        'O1_PLA':models.PLA.objects.all().filter(bloodStock__bloodgroup="O+"),

        'A1_PSM':models.PSM.objects.all().filter(bloodStock__bloodgroup="A+"),
        'B1_PSM':models.PSM.objects.all().filter(bloodStock__bloodgroup="B+"),
        'AB1_PSM':models.PSM.objects.all().filter(bloodStock__bloodgroup="AB+"),
        'O1_PSM':models.PSM.objects.all().filter(bloodStock__bloodgroup="O+"),

        'A1_RBC':models.RBC.objects.all().filter(bloodStock__bloodgroup="A+"),
        'B1_RBC':models.RBC.objects.all().filter(bloodStock__bloodgroup="B+"),
        'AB1_RBC':models.RBC.objects.all().filter(bloodStock__bloodgroup="AB+"),
        'O1_RBC':models.RBC.objects.all().filter(bloodStock__bloodgroup="O+"),

        'A1_WBC':models.WBC.objects.all().filter(bloodStock__bloodgroup="A+"),
        'B1_WBC':models.WBC.objects.all().filter(bloodStock__bloodgroup="B+"),
        'AB1_WBC':models.WBC.objects.all().filter(bloodStock__bloodgroup="AB+"),
        'O1_WBC':models.WBC.objects.all().filter(bloodStock__bloodgroup="O+"),
    }
    if request.method == 'POST' and request.POST.get('type') == 'bloodUnit':
        
        # Units
        bla_units = request.POST.get('bunit')

        # Receiving Date
        bla_receiving_date = request.POST.get('breceive_date')

        # Expiration Date
        bla_expiration_date = request.POST.get('bexpiration_date')

        bloodGroup = request.POST.get('bloodgroup')

        # Process
        for x in range(int(bla_units)):
        
        # Create new Blood Unit
            bla = models.BLA()
            bla.unit = 1
            bla.expiration_date = bla_expiration_date
            bla.receive_date = bla_receiving_date
            bla.bloodStock = models.Stock.objects.get(bloodgroup=bloodGroup)
            bla.save()

    elif request.method == 'POST' and request.POST.get('type') == 'rbc':
        
        rbc_units = request.POST.get('runit')
        bloodGroup = request.POST.get('bloodgroup')
        rbc_receiving_date = request.POST.get('rreceive_date')
        rbc_expiration_date = request.POST.get('rexpiration_date')

        for y in range(int(rbc_units)):
            rbc = models.RBC()
            rbc.bloodStock = models.Stock.objects.get(bloodgroup=bloodGroup)
            rbc.receive_date = rbc_receiving_date
            rbc.expiration_date = rbc_expiration_date
            rbc.save()
    
    elif request.method == 'POST' and request.POST.get('type') == 'wbc':
        
        wbc_units = request.POST.get('wunit')
        bloodGroup = request.POST.get('bloodgroup')
        wbc_receiving_date = request.POST.get('wreceive_date')
        wbc_expiration_date = request.POST.get('wexpiration_date')
        
        for y in range(int(wbc_units)):
            wbc = models.WBC()
            wbc.bloodStock = models.Stock.objects.get(bloodgroup=bloodGroup)
            wbc.receive_date = wbc_receiving_date
            wbc.expiration_date = wbc_expiration_date
            wbc.save()
    
    elif request.method == 'POST' and request.POST.get('type') == 'psm':
        
        psm_units = request.POST.get('psunit')
        bloodGroup = request.POST.get('bloodgroup')
        psm_receiving_date = request.POST.get('psreceive_date')
        psm_expiration_date = request.POST.get('psexpiration_date')
        
        for y in range(int(psm_units)):
            psm = models.PSM()
            psm.bloodStock = models.Stock.objects.get(bloodgroup=bloodGroup)
            psm.receive_date = psm_receiving_date
            psm.expiration_date = psm_expiration_date
            psm.save()
    
    elif request.method == 'POST' and request.POST.get('type') == 'pla':
        
        pla_units = request.POST.get('plunit')
        bloodGroup = request.POST.get('bloodgroup')
        pla_receiving_date = request.POST.get('plreceive_date')
        pla_expiration_date = request.POST.get('plexpiration_date')
        
        for y in range(int(pla_units)):
            pla = models.PLA()
            pla.bloodStock = models.Stock.objects.get(bloodgroup=bloodGroup)
            pla.receive_date = pla_receiving_date
            pla.expiration_date = pla_expiration_date
            pla.save()

        return HttpResponseRedirect('admin-blood')
        
        
    return render(request,'blood/admin_blood.html',context=dict)


@login_required(login_url='adminlogin')
def admin_donor_view(request):
    donors=dmodels.Donor.objects.all().select_related('user')
    return render(request,'blood/admin_donor.html',{'donors':donors})

@login_required(login_url='adminlogin')
def update_donor_view(request,pk):
    donor=dmodels.Donor.objects.get(id=pk)
    user=dmodels.User.objects.get(id=donor.user_id)
    userForm=dforms.DonorUserForm(instance=user)
    donorForm=dforms.DonorForm(request.FILES,instance=donor)
    mydict={'userForm':userForm,'donorForm':donorForm}
    if request.method=='POST':
        userForm=dforms.DonorUserForm(request.POST,instance=user)
        donorForm=dforms.DonorForm(request.POST,request.FILES,instance=donor)
        if userForm.is_valid() and donorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            donor=donorForm.save(commit=False)
            donor.user=user
            donor.bloodgroup=donorForm.cleaned_data['bloodgroup']
            donor.save()
            return redirect('admin-donor')
    return render(request,'blood/update_donor.html',context=mydict)


@login_required(login_url='adminlogin')
def delete_donor_view(request,pk):
    donor=dmodels.Donor.objects.get(id=pk)
    user=User.objects.get(id=donor.user_id)
    user.delete()
    donor.delete()
    return HttpResponseRedirect('/admin-donor')

@login_required(login_url='adminlogin')
def admin_patient_view(request):
    patients=pmodels.Patient.objects.all()
    return render(request,'blood/admin_patient.html',{'patients':patients})


@login_required(login_url='adminlogin')
def update_patient_view(request,pk):
    patient=pmodels.Patient.objects.get(id=pk)
    user=pmodels.User.objects.get(id=patient.user_id)
    userForm=pforms.PatientUserForm(instance=user)
    patientForm=pforms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=pforms.PatientUserForm(request.POST,instance=user)
        patientForm=pforms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.bloodgroup=patientForm.cleaned_data['bloodgroup']
            patient.save()
            return redirect('admin-patient')
    return render(request,'blood/update_patient.html',context=mydict)


@login_required(login_url='adminlogin')
def delete_patient_view(request,pk):
    patient=pmodels.Patient.objects.get(id=pk)
    user=User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return HttpResponseRedirect('/admin-patient')

@login_required(login_url='adminlogin')
def admin_request_view(request):
    bloodRequests=models.BloodRequest.objects.all().filter(status='Pending')
    for bloodRequest in bloodRequests:
        if(bloodRequest.request_by_patient_id != None):
            patient = pmodels.Patient.objects.get(id=bloodRequest.request_by_patient_id)
            bloodRequest.mobile = patient.mobile
        else:
            donor = dmodels.Donor.objects.get(id=bloodRequest.request_by_donor_id)
            bloodRequest.mobile = donor.mobile

    app_url = settings.APP_URL
    return render(request,'blood/admin_request.html',context={'app_url':app_url,'requests':bloodRequests})

@login_required(login_url='adminlogin')
def admin_request_history_view(request):
    requests=models.BloodRequest.objects.all().exclude(status='Pending')
    return render(request,'blood/admin_request_history.html',{'requests':requests})

@login_required(login_url='adminlogin')
def admin_donation_view(request):
    blood_test_upload = False
    donations=dmodels.BloodDonate.objects.all()
    if 'blood_test_upload' in request.session:
        blood_test_upload = request.session['blood_test_upload']
        del request.session['blood_test_upload']
    return render(request,'blood/admin_donation.html',context={'donations':donations,'blood_test_upload':blood_test_upload})

def sendEmail(receiver_address,subject,mail_content):
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject # The subject line
    # The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_pass)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')
@login_required(login_url='adminlogin')
def update_approve_status_view(request,pk,units):
    # Setup the MIME
    req=models.BloodRequest.objects.get(id=pk)
    receiver_address = ""
    if(req.request_by_patient != None):
        receiver_address = req.request_by_patient.user.email
    else:
        receiver_address = req.request_by_donor.user.email
    message=None
    bloodgroup=req.bloodgroup
    unit=units
    stock=models.Stock.objects.get(bloodgroup=bloodgroup)
    donor_id = req.request_by_donor_id
    user_id = dmodels.Donor.objects.get(id=donor_id).user_id
    userID = User.objects.get(id=user_id)
    if stock.unit > unit:
        stock.unit=stock.unit-unit
        stock.save()
        req.unit_approved = units
        req.status="Approved"
        new_notif = dmodels.Notification(user=userID, message="Blood request approved, we are able to donate " + str(units) + " units")
        new_notif.save()
        sendEmail(receiver_address, "Blood request approved","We are able to donate " + str(units) + " units")

    else:
        message="Stock Doest Not Have Enough Blood To Approve This Request, Only "+str(stock.unit)+" Unit Available"
    req.save()

    requests=models.BloodRequest.objects.all().filter(status='Pending')
    return render(request,'blood/admin_request.html',{'requests':requests,'message':message})

@login_required(login_url='adminlogin')
def update_reject_status_view(request,pk):
    req=models.BloodRequest.objects.get(id=pk)
    req.status="Rejected"
    req.save()
    receiver_address = ""
    donor_id = req.request_by_donor_id
    user_id = dmodels.Donor.objects.get(id=donor_id).user_id
    userID = User.objects.get(id=user_id)
    if (req.request_by_patient != None):
        receiver_address = req.request_by_patient.user.email
        print("theemail" + receiver_address)

    else:
        receiver_address = req.request_by_donor.user.email
        print("theemail" + receiver_address)

    print("theemail" + receiver_address)
    new_notif = dmodels.Notification(user=userID, message="Blood request rejected, we are not able to approve your blood request")
    new_notif.save()
    sendEmail(receiver_address, "Blood request rejected", "We are not able to approve your blood request")
    return HttpResponseRedirect('/admin-request')

@login_required(login_url='adminlogin')
def approve_donation_view(request,pk):
    donation=dmodels.BloodDonate.objects.get(id=pk)
    donation_blood_group=donation.bloodgroup
    donation_blood_unit=donation.unit

    donor_id = donation.donor_id
    user_id = dmodels.Donor.objects.get(id=donor_id).user_id
    userID = User.objects.get(id=user_id)
    
    stock=models.Stock.objects.get(bloodgroup=donation_blood_group)
    stock.unit=100
    print("the units " + str(stock.unit))
    stock.save()

    donation.status='Approved'
    new_notif = dmodels.Notification(user=userID, message="Your blood donation has been approved")
    new_notif.save()
    donation.save()
    return HttpResponseRedirect('/admin-donation')

def blood_test(request,pk):
    blood_test_form = forms.BloodTestForm()
    bloodgroupform = dforms.BloodGroupForm()
    bloodTest = models.BloodTest.objects.filter(bloodDonate_id=pk)
    if request.method == 'POST':
        request_form = forms.BloodTestForm(request.POST)
        if(len(bloodTest) > 0):
            bloodTest = models.BloodTest.objects.get(bloodDonate_id=pk)
            request_form = forms.BloodTestForm(request.POST,instance=bloodTest)
        if request_form.is_valid():
            announcement_request = request_form.save(commit=False)

            announcement_request.bloodDonate_id = pk
            approve = True
            for val in announcement_request.__dict__.items():
                # print(type(val[1]))
                if(type(val[1]) == bool):
                    if(val[1]):
                        approve = False
            if approve:
                donation = dmodels.BloodDonate.objects.get(id=pk)
                donor_id = donation.donor_id
                user_id = dmodels.Donor.objects.get(id=donor_id).user_id
                userID = User.objects.get(id=user_id)
                donation_blood_group = donation.bloodgroup
                donation.unit = request_form.cleaned_data['unit']
                donation.save()
                donation_blood_unit = donation.unit
                stock = models.Stock.objects.get(bloodgroup=donation_blood_group)
                print("stock unit " + str(stock.unit) + " donation unit " + str(donation_blood_unit))
                stock.unit = stock.unit + donation_blood_unit
                stock.save()
                donation.status = 'Approved'
                donation.save()
                new_notif = dmodels.Notification(user=userID, message="Your blood donation has been approved")
                new_notif.save()
                request.session['blood_test_upload'] = 'approved'
            else:
                donation = dmodels.BloodDonate.objects.get(id=pk)
                donor_id = donation.donor_id
                user_id = dmodels.Donor.objects.get(id=donor_id).user_id
                userID = User.objects.get(id=user_id)
                donation.status = 'Rejected'
                donation.save()
                new_notif = dmodels.Notification(user=userID, message="Your blood donation has been rejected")
                new_notif.save()
                request.session['blood_test_upload'] = 'not approved'
            announcement_request.save()
            return HttpResponseRedirect('/admin-donation')
        
        request.session['blood_test_upload'] = False
        return HttpResponseRedirect('/admin-donation')
    
    bloodDonation = dmodels.BloodDonate.objects.get(id=pk)
    survey_answers = []
    user_info = dict((x, y) for x, y in dmodels.Donor.objects.values().get(id=dmodels.BloodDonate.objects.get(id=pk).donor_id).items())
    
    for k,v in bloodDonation.survey_answer.items():
        if(k != "csrfmiddlewaretoken"):
            survey_answers.append({"key": k, "value": v})
    
    user_id = user_info['user_id']
    firstname = User.objects.get(id=user_id).first_name
    lastname = User.objects.get(id=user_id).last_name
    user_info['firstname'] = firstname
    user_info['lastname'] = lastname

    user_id_pk = {"user_id_pk": str(pk)}
    # print(user_id_pk)

    return render(request, 'blood/admin_blood_test.html',context={'blood_test_form':blood_test_form,'survey_answers':survey_answers,'user_info':user_info,'bloodgroupform':bloodgroupform,'user_id_pk':user_id_pk})

@login_required(login_url='adminlogin')
def reject_donation_view(request,pk):
    donation=dmodels.BloodDonate.objects.get(id=pk)
    donor_id = donation.donor_id
    user_id = dmodels.Donor.objects.get(id=donor_id).user_id
    userID = User.objects.get(id=user_id)
    donation.status='Rejected'
    donation.save()
    new_notif = dmodels.Notification(user=userID, message="Your blood donation has been rejected")
    new_notif.save()
    return HttpResponseRedirect('/admin-donation')
