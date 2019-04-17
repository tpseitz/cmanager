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
var DRAG_CLASS = "computer";
var REGEX_TRANSLATE = /translate\(\s*(\d+)\s*,\s*(\d+)\s*\)/;

var svg = null;
var dragged = null;
var offset = null;

function getMouseLocation(vnt) {
  var ctm = svg.getScreenCTM()
  var pt = svg.createSVGPoint();
  pt.x = (vnt.clientX - ctm.e) / ctm.a;
  pt.y = (vnt.clientY - ctm.f) / ctm.d;
  return pt;
}

function mouseDown(vnt) {
  console.debug(getMouseLocation(vnt)); //XXX

  target = vnt.target;
  cnt = 0;
  while (target && cnt < 50) {
    cnt++;
    if (target.classList && target.classList.contains(DRAG_CLASS)) break;
    target = target.parentNode;
    if (target == svg) { target = null; break; }
  }

  if (target) {
    vnt.preventDefault();
    dragged = target;
    mt = REGEX_TRANSLATE.exec(target.getAttribute('transform'));
    if (mt) {
      offset = getMouseLocation(vnt);
      offset.x -= parseInt(mt[1]);
      offset.y -= parseInt(mt[2]);
    }
  }
}

function mouseUp()  {
  if (dragged && offset) {
    mt = REGEX_TRANSLATE.exec(dragged.getAttribute('transform'));
    var x, y;
    if (mt) { x = parseInt(mt[1]); y = parseInt(mt[2]); }
    var url = SCRIPT + '/update/' + dragged.id + '/' + x + '/' + y;
    var http = new XMLHttpRequest();
    http.open('GET', url, true);
    http.send(null);
  }
  offset = null; dragged = null;
}

function mouseMove(vnt) {
  if (dragged && offset) {
    vnt.preventDefault();
    pt = getMouseLocation(vnt);
    pt.x = pt.x - offset.x;
    pt.y = pt.y - offset.y;
    trn = 'translate(' + parseInt(pt.x) + ', ' + parseInt(pt.y) + ')';
    dragged.setAttribute('transform', trn);
  }
}

function init(vnt) {
  svg = vnt.target;
  svg.addEventListener('mousedown',  mouseDown);
  svg.addEventListener('mousemove',  mouseMove);
  svg.addEventListener('mouseup',    mouseUp);
  svg.addEventListener('mouseleave', mouseUp);
}
