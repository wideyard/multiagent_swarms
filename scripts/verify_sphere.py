"""
Verify whether a set of 3D points approximately lie on a sphere.

Usage:
    python scripts/verify_sphere.py PATH_TO_JSON

Default file: outputs/goals_10_20260111_230221.json

The script:
 - loads the JSON with key `goals_ned` as list of [x,y,z]
 - fits a sphere using linear least-squares
 - computes residuals (distance from fitted sphere surface)
 - prints metrics and a PASS/FAIL judgement
 - saves results to <input>_sphere_check.json
"""

import json
import os
import argparse
import numpy as np


def load_goals(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pts = np.array(data.get("goals_ned", []), dtype=float)
    return pts, data


def fit_sphere(points):
    # Solve for center (cx,cy,cz) and c where
    # (x^2+y^2+z^2) = 2*cx*x + 2*cy*y + 2*cz*z + c
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    A = np.column_stack([2 * x, 2 * y, 2 * z, np.ones_like(x)])
    b = x * x + y * y + z * z
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy, cz, c = sol
    center = np.array([cx, cy, cz])
    radius = np.sqrt(max(0.0, cx * cx + cy * cy + cz * cz + c))
    dists = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
    residuals = np.abs(dists - radius)
    return center, radius, residuals, dists


def evaluate(points3d, data=None, verbose=True):
    n = points3d.shape[0]
    if n < 4:
        raise ValueError("Need at least 4 non-coplanar points to robustly define a sphere")

    center, R, residuals, dists = fit_sphere(points3d)

    metrics = {
        "num_points": int(n),
        "fitted_center": center.tolist(),
        "radius": float(R),
        "residuals": residuals.tolist(),
        "residuals_rms": float(np.sqrt(np.mean(residuals ** 2))),
        "residuals_max": float(np.max(residuals)),
    }

    # thresholds relative to radius
    R_ref = max(1e-6, R)
    tol_rms = max(0.02 * R_ref, 0.05)   # RMS residual allowed
    tol_max = max(0.05 * R_ref, 0.1)    # max residual allowed

    pass_rms = metrics["residuals_rms"] <= tol_rms
    pass_max = metrics["residuals_max"] <= tol_max
    verdict = pass_rms and pass_max

    if verbose:
        print("Sphere fit results:")
        if data and data.get("description"):
            print(f"  Description: {data.get('description')}")
        print(f"  Num points: {metrics['num_points']}")
        print(f"  Fitted center: {metrics['fitted_center']}")
        print(f"  Radius: {metrics['radius']:.4f}")
        print(f"  Residuals RMS: {metrics['residuals_rms']:.4f}   Max: {metrics['residuals_max']:.4f}")
        print("\nThresholds used:")
        print(f"  tol_rms = {tol_rms:.4f} (RMS allowed)")
        print(f"  tol_max = {tol_max:.4f} (max allowed)")
        print("\nVerdict: {}".format("PASS (points form an approximate sphere)" if verdict else "FAIL (points do not form a sphere)"))

    return verdict, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.path.join("outputs", "goals_10_20260111_230221.json"),
                        help="Path to goals JSON file")

    args = parser.parse_args()

    pts, data = load_goals(args.path)
    if pts.size == 0:
        print("No points found in JSON 'goals_ned'")
        return 2

    try:
        verdict, metrics = evaluate(pts, data)
    except Exception as e:
        print(f"Error evaluating points: {e}")
        return 2

    out_path = os.path.splitext(args.path)[0] + "_sphere_check.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"verdict": bool(verdict), "metrics": metrics}, f, indent=2, ensure_ascii=False)
        print(f"Saved results to {out_path}")
    except Exception as e:
        print(f"Could not save results: {e}")

    return 0


if __name__ == "__main__":
    main()
