### Base dito sa code na ito.
```js
new gridjs.Grid({
  columns: [{name: "ID", hidden: true},"ID No.", "Receiving Date", "Expiration Date",{ name: "Actions", formatter: (_, row) => gridjs.html(
    `
    <button class="btn btn-warning btn-sm" data-toggle="modal" data-target="#editBloodA1-${row.cells[0].data}">Edit</button> <button type="button" class="btn btn-danger btn-sm" onclick="window.location='deleteUnit/${row.cells[0].data}'">Delete</button>
    <div class="modal fade" id="editBloodA1-${row.cells[0].data}" tabindex="-1" role="dialog" data-backdrop="true">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h4 class="modal-title">Edit Whole Blood Unit A+ (${row.cells[1].data})</h4>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close" data-target="#editBloodA1-${row.cells[0].data}">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <form action="" method="POST">
            {% csrf_token %}
            <input type="hidden" name="bloodgroup" value="A+" />
            <input type="hidden" name="type" value="bloodUnit" />
            <input type="hidden" name="edit" value="1" />
            <input type="hidden" name="bloodUnit" value="${row.cells[0].data}"/>
            <div class="modal-body">
              <div class="row">
                <div class="col-4">
                  <div class="my-3">
                    <label class="form-label">
                      Receiving Date
                    </label>
                    <input type="date" class="form-control" name="breceive_date" required value="${new Date(row.cells[2].data.replace(/(\d{1,2})(st|nd|rd|th)/, '$1')).toISOString().slice(0, 10)}"/>
                  </div>
                </div>
                <div class="col-4">
                  <div class="my-3">
                    <label class="form-label">
                      Expiration Date
                    </label>
                    <input type="date" class="form-control" name="bexpiration_date" required value="${new Date(row.cells[3].data.replace(/(\d{1,2})(st|nd|rd|th)/, '$1')).toISOString().slice(0, 10)}"/>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="submit" class="btn btn-success">Save</button>
          </form>
        </div>
      </div>
    </div>
    `
    ) }
  ],
  search: false,
  data: [
    {% for a in A1 %}
      ['{{a.id}}','BD-{{a.id|stringformat:"08d"|add:""}}', '{{a.receive_date}}', '{{a.expiration_date}}', null],
    {% endfor %}
  ]
}).render(document.getElementById("bloodA+"));
```

### Gusto ko gawin ang same idea para sa mga grid table shit neto

```js
render(document.getElementById("PSMB+"));
render(document.getElementById("PLAB+"));
render(document.getElementById("WBCB+"));
render(document.getElementById("RBCB+"));
render(document.getElementById("PSMAB+"));
render(document.getElementById("PLAAB+"));
render(document.getElementById("WBCAB+"));
render(document.getElementById("RBCAB+"));
render(document.getElementById("PSMO+"));
render(document.getElementById("PLAO+"));
render(document.getElementById("WBCO+"));
render(document.getElementById("RBCO+"));
render(document.getElementById("PSMA+"));
render(document.getElementById("PLAA+"));
render(document.getElementById("WBCA+"));
render(document.getElementById("RBCA+"));
```
