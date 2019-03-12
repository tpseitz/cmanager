var col = -1;
var ord = -1;
var imgls = [];

function sortBy(vnt) {
  var elm = vnt.target;
  for (var i = 0; i < imgls.length; i++) imgls[i].src = 'sort-none.svg';
  if (col != elm.column) ord = -1;
  col = elm.column;
  ord = (ord + 1) % 2;
  if (ord == 0) {
    elm.lastChild.src = 'sort-asc.svg';
  } else {
    elm.lastChild.src = 'sort-desc.svg';
  }
}

function setupSort(table, columns) {
  var tbl = document.getElementById(table);
  if (tbl == null) {
    console.log('No table named ' + table);
    return;
  }
  var fr = tbl.getElementsByTagName('tr')[0];
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

