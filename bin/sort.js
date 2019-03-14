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

