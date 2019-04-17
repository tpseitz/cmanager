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

var REGEX_NUMBER = /^\d+(\.\d+)?$/;

var col = -1;
var ord = -1;
var imgls = [];

function sortBy(vnt) {
  var elm = vnt.target;
  for (var i = 0; i < imgls.length; i++) imgls[i].src = 'sort-none.svg';
  if (col != elm.column) ord = -1;
  col = elm.column;
  ord = (ord + 1) % 2;

  var tbl = elm;
  while (tbl && tbl.tagName != 'TABLE') tbl = tbl.parentElement;
  if (!tbl) {
    console.log('No parent table');
    return false;
  }
  var rows = tbl.rows;

  var ascenting = true;
  if (ord == 0) {
    elm.lastChild.src = 'sort-asc.svg';
    ascending = true;
  } else {
    elm.lastChild.src = 'sort-desc.svg';
    ascending = false;
  }

  var sorting = true;
  var r1, r2, c1, c2, t1, t2, swap;
  while (sorting) {
    sorting = false;
    for (var i = 1; i < rows.length - 1; i++) {
      r1 = rows[i];
      r2 = rows[i + 1];

      c1 = r1.getElementsByTagName('td')[col];
      c2 = r2.getElementsByTagName('td')[col];

      while (c1.firstElementChild) c1 = c1.firstElementChild;
      while (c2.firstElementChild) c2 = c2.firstElementChild;
      t1 = c1.innerHTML.toLowerCase();
      t2 = c2.innerHTML.toLowerCase();

      if (REGEX_NUMBER.test(t1) || REGEX_NUMBER.test(t2)) {
        if (REGEX_NUMBER.test(t1)) t1 = Number(t1);
        else t1 = 0;
        if (REGEX_NUMBER.test(t2)) t2 = Number(t2);
        else t2 = 0;
      }

      swap = false;
      if (ascending && t1 > t2) swap = true;
      if (!ascending && t1 < t2) swap = true;
      if (swap) {
        r1.parentNode.insertBefore(r2, r1);
        sorting = true;
      }
    }
  }
}

function setupSort(table, columns) {
  var tbl = document.getElementById(table);
  if (tbl == null) {
    console.log('No table named ' + table);
    return;
  }
  var fr = tbl.rows[0];
  var hls = fr.getElementsByTagName('th');
  if (!hls.length == 0) fr.getElementsByTagName('td');
  if (!hls) console.log('No headers!');
  for (var l = 0; l < columns.length; l++) {
    var elm = hls[columns[l]];
    img = document.createElement('img');
    img.classList.add('sort');
    img.src = 'sort-none.svg'
    elm.appendChild(img);
    elm.column = columns[l];
    elm.onclick = sortBy;
    imgls[imgls.length] = img;
  }
}

