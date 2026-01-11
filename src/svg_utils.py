"""
Utilities to parse simple SVG outlines and uniformly sample contour points.

Supports primitive elements: <path> (M,L,H,V,Z,C), <circle>, <rect>, <polygon>, <polyline>.
Provides `parse_and_sample(svg_text, num_points)` -> ndarray (N,3).
"""
from xml.etree import ElementTree as ET
import re
import math
import numpy as np


def _parse_floats(s):
    return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", s)]


def _cubic_bezier(p0, p1, p2, p3, t):
    return (
        (1 - t) ** 3 * np.array(p0)
        + 3 * (1 - t) ** 2 * t * np.array(p1)
        + 3 * (1 - t) * t ** 2 * np.array(p2)
        + t ** 3 * np.array(p3)
    )


def _sample_cubic(p0, p1, p2, p3, n=20):
    ts = np.linspace(0, 1, n)
    return [_cubic_bezier(p0, p1, p2, p3, t) for t in ts]


def _segment_length(pts):
    pts = np.array(pts)
    if len(pts) < 2:
        return 0.0
    return np.sum(np.linalg.norm(pts[1:] - pts[:-1], axis=1))


def _resample_along(points, num_points):
    pts = np.array(points)
    if pts.shape[0] == 0:
        return pts
    # compute cumulative lengths
    dists = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
    cum = np.concatenate([[0.0], np.cumsum(dists)])
    total = cum[-1]
    if total == 0:
        # all points identical
        out = np.tile(pts[0], (num_points, 1))
        return out
    # desired distances
    desired = np.linspace(0, total, num_points, endpoint=False)
    out = []
    for s in desired:
        # find segment
        idx = np.searchsorted(cum, s, side='right') - 1
        if idx < 0:
            idx = 0
        if idx >= len(pts) - 1:
            out.append(pts[-1])
            continue
        t = (s - cum[idx]) / (cum[idx + 1] - cum[idx]) if cum[idx + 1] > cum[idx] else 0.0
        p = (1 - t) * pts[idx] + t * pts[idx + 1]
        out.append(p)
    return np.array(out)


def _parse_path_d(d):
    # Very small path parser for commands: M,L,H,V,Z,C (absolute or relative)
    tokens = re.findall(r'[MmLlHhVvCcZz]|-?\d+\.?\d*(?:[eE][+-]?\d+)?', d)
    cmds = []
    i = 0
    current_cmd = None
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r'[MmLlHhVvCcZz]', tok):
            current_cmd = tok
            i += 1
        else:
            # implicit command repetition
            pass
        cmd = current_cmd
        if cmd in ('M', 'm', 'L', 'l'):
            # pairs
            nums = []
            while i < len(tokens) and not re.match(r'[A-Za-z]', tokens[i]):
                nums.append(float(tokens[i])); i += 1
            pts = [(nums[j], nums[j+1]) for j in range(0, len(nums), 2)]
            for p in pts:
                cmds.append((cmd, p))
                # subsequent pairs after M are treated as L according to spec
                if cmd in ('M', 'm'):
                    cmd = 'L' if cmd == 'M' else 'l'
        elif cmd in ('H', 'h'):
            nums = []
            while i < len(tokens) and not re.match(r'[A-Za-z]', tokens[i]):
                nums.append(float(tokens[i])); i += 1
            for x in nums:
                cmds.append((cmd, x))
        elif cmd in ('V', 'v'):
            nums = []
            while i < len(tokens) and not re.match(r'[A-Za-z]', tokens[i]):
                nums.append(float(tokens[i])); i += 1
            for y in nums:
                cmds.append((cmd, y))
        elif cmd in ('C', 'c'):
            nums = []
            while i < len(tokens) and not re.match(r'[A-Za-z]', tokens[i]):
                nums.append(float(tokens[i])); i += 1
            triples = [(nums[j], nums[j+1], nums[j+2], nums[j+3], nums[j+4], nums[j+5]) for j in range(0, len(nums), 6)]
            for tset in triples:
                p1 = (tset[0], tset[1]); p2 = (tset[2], tset[3]); p3 = (tset[4], tset[5])
                cmds.append((cmd, (p1, p2, p3)))
        elif cmd in ('Z', 'z'):
            cmds.append((cmd, None))
            i += 0
        else:
            i += 1
    return cmds


def _path_to_points(d, samples_per_curve=30):
    cmds = _parse_path_d(d)
    pts = []
    cur = np.array([0.0, 0.0])
    start = None
    for cmd, val in cmds:
        if cmd == 'M':
            cur = np.array(val)
            start = cur.copy()
            pts.append(cur.copy())
        elif cmd == 'm':
            cur = cur + np.array(val)
            start = cur.copy()
            pts.append(cur.copy())
        elif cmd == 'L':
            cur = np.array(val);
            pts.append(cur.copy())
        elif cmd == 'l':
            cur = cur + np.array(val); pts.append(cur.copy())
        elif cmd == 'H':
            cur = np.array([val, cur[1]]); pts.append(cur.copy())
        elif cmd == 'h':
            cur = cur + np.array([val, 0]); pts.append(cur.copy())
        elif cmd == 'V':
            cur = np.array([cur[0], val]); pts.append(cur.copy())
        elif cmd == 'v':
            cur = cur + np.array([0, val]); pts.append(cur.copy())
        elif cmd in ('C', 'c'):
            p1, p2, p3 = val
            if cmd == 'C':
                ps = _sample_cubic(cur, p1, p2, p3, n=samples_per_curve)
            else:
                # relative
                p1_abs = cur + np.array(p1)
                p2_abs = cur + np.array(p2)
                p3_abs = cur + np.array(p3)
                ps = _sample_cubic(cur, p1_abs, p2_abs, p3_abs, n=samples_per_curve)
            for q in ps[1:]:
                pts.append(np.array(q))
            cur = np.array(p3 if cmd == 'C' else p3_abs)
        elif cmd in ('Z', 'z'):
            if start is not None:
                pts.append(start.copy())
                cur = start.copy()
    # ensure numeric array
    if len(pts) == 0:
        return np.empty((0,2))
    arr = np.vstack([np.array(p, dtype=float) for p in pts])
    return arr


def parse_and_sample(svg_text: str, num_points: int) -> np.ndarray:
    """
    Parse SVG text, extract primary contour(s), and return `num_points` uniformly sampled 3D points (z=0).
    """
    try:
        root = ET.fromstring(svg_text)
    except Exception:
        # try to wrap
        try:
            svg_text = '<svg>' + svg_text + '</svg>'
            root = ET.fromstring(svg_text)
        except Exception:
            return np.empty((0,3))

    # collect dense contour points
    contours = []
    # namespace handling
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        if tag == 'path' and 'd' in elem.attrib:
            d = elem.attrib.get('d')
            pts = _path_to_points(d)
            if pts.size:
                contours.append(pts)
        elif tag == 'circle':
            cx = float(elem.attrib.get('cx', '0'))
            cy = float(elem.attrib.get('cy', '0'))
            r = float(elem.attrib.get('r', '1'))
            angles = np.linspace(0, 2*math.pi, max(64, num_points*2), endpoint=False)
            x = cx + r * np.cos(angles)
            y = cy + r * np.sin(angles)
            pts = np.stack([x, y], axis=1)
            contours.append(pts)
        elif tag in ('rect',):
            x = float(elem.attrib.get('x','0'))
            y = float(elem.attrib.get('y','0'))
            w = float(elem.attrib.get('width','1'))
            h = float(elem.attrib.get('height','1'))
            pts = np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y]])
            contours.append(pts)
        elif tag in ('polygon','polyline') and 'points' in elem.attrib:
            pts_list = _parse_floats(elem.attrib.get('points',''))
            pts = np.array([(pts_list[i], pts_list[i+1]) for i in range(0, len(pts_list), 2)])
            contours.append(pts)

    if not contours:
        return np.empty((0,3))

    # choose the longest contour (most points) as primary
    lens = [c.shape[0] for c in contours]
    main = contours[np.argmax(lens)]

    # resample uniformly along contour
    sampled2d = _resample_along(main, num_points)
    # return Nx3 with z=0
    out3 = np.zeros((sampled2d.shape[0], 3), dtype=float)
    out3[:, 0:2] = sampled2d
    return out3