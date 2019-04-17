/*
Lisence (BSD License 2.0)

Copyright (c) 2018, 2019 Timo Seitz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

var SCRIPT = '{{script}}';
var REGEX_NUMBER = /^\s*\d+(\.\d+)?\s*$/;
var REGEX_COMMENT = /<\!--(.+)-->/;

function moveRow(vnt) {
  var elm = vnt.currentTarget
  var row = elm.row;
  var table = row.table;
  var url = SCRIPT + '/update/' + row.identifier;
  if (elm.forward) {
    if (row.next) row.parentNode.insertBefore(row, row.next.nextSibling);
    url += '/down';
  } else {
    if (row.prev) row.parentNode.insertBefore(row, row.prev);
    url += '/up';
  }
  var http = new XMLHttpRequest();
  http.open('GET', url, true);
  http.send(null);

  initMove(table);
}

function initMove(table) {
  var tbl = table;
  if (typeof table == 'string') tbl = document.getElementById(table);
  var rows = Array.from(tbl.rows);
  if (rows[0].children[0].tagName.toLowerCase() == 'th')
    rows = rows.slice(1);
  if (rows[rows.length-1].children[0].getElementsByClassName('up').length <= 0)
    rows = rows.slice(0, -1);

  for (var index = 0; index < rows.length; index++) {
    var row = rows[index];
    var up = rows[index].getElementsByClassName('up');
    var down = rows[index].getElementsByClassName('down');
    if (up.length != 1 || down.length != 1) continue;
    up = up[0];
    down = down[0];

    var tdls = row.getElementsByTagName('td');
    if (tdls.length == 0) continue;
    var td = tdls[0];
    while (td.firstChild) td = td.firstChild;
    var id = td.textContent || td.innerText || "";
    if (REGEX_NUMBER.test(id)) id = Number(id);
    row.identifier = id;

    up.onclick = moveRow;
    up.row = row;
    up.forward = false;
    down.onclick = moveRow;
    down.row = row;
    down.forward = true;

    row.table = tbl;
    if (index != 0) row.prev = rows[index - 1];
    else row.prev = null;
    if (index != rows.length - 1) row.next = rows[index + 1];
    else row.next = null;

    if (!row.prev) up.style.display = 'none';
    else up.style.display = 'initial';
    if (!row.next) down.style.display = 'none';
    else down.style.display = 'initial';
  }
}
