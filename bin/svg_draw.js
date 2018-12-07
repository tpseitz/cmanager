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

function mouseUp(vnt)  { offset = null; dragged = null; }

function mouseMove(vnt) {
  if (dragged && offset) {
    vnt.preventDefault();
    pt = getMouseLocation(vnt);
    if (offset) {
      pt.x = pt.x - offset.x;
      pt.y = pt.y - offset.y;
    }
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
