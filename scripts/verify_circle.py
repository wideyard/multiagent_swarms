"""
Verify whether a set of 3D points approximately lie on a circle.

Usage:
    python scripts/verify_circle.py PATH_TO_JSON

Default file: outputs/goals_10_20260111_230221.json

The script:
 - loads the JSON with key `goals_ned` as list of [x,y,z]
 - fits a best-fit plane via SVD
 - projects points to plane coordinates
 - fits a 2D circle (least-squares)
 - computes residuals and coplanarity distances
 - prints metrics and a simple PASS/FAIL based on tolerances
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


def fit_plane(points):
    # returns centroid, normal, basis_u, basis_v
    centroid = points.mean(axis=0)
    X = points - centroid
    u, s, vh = np.linalg.svd(X, full_matrices=False)
    normal = vh[-1]
    # choose first basis vector in plane
    basis_u = vh[0]
    basis_v = np.cross(normal, basis_u)
    # normalize
    basis_u = basis_u / np.linalg.norm(basis_u)
    basis_v = basis_v / np.linalg.norm(basis_v)
    return centroid, normal, basis_u, basis_v


def project_to_plane(points, centroid, basis_u, basis_v):
    X = points - centroid
    x_coords = X.dot(basis_u)
    y_coords = X.dot(basis_v)
    return np.vstack([x_coords, y_coords]).T


def fit_circle_2d(xy):
    # Solve (xi^2+yi^2) = 2a xi + 2b yi + c
    x = xy[:, 0]
    y = xy[:, 1]
    A = np.column_stack([2 * x, 2 * y, np.ones_like(x)])
    b = x * x + y * y
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    a, b_par, c = sol
    center = np.array([a, b_par])
    radius = np.sqrt(max(0.0, a * a + b_par * b_par + c))
    # residuals
    dists = np.sqrt((x - a) ** 2 + (y - b_par) ** 2)
    residuals = np.abs(dists - radius)
    return center, radius, residuals, dists


def evaluate(points3d, data=None, verbose=True):
    if points3d.shape[0] < 3:
        raise ValueError("Need at least 3 points to define a circle")

    centroid, normal, u, v = fit_plane(points3d)
    xy = project_to_plane(points3d, centroid, u, v)
    center2d, R, residuals, dists = fit_circle_2d(xy)

    # center in 3D
    center3d = centroid + center2d[0] * u + center2d[1] * v

    # coplanarity distances
    coplanar_dists = np.abs((points3d - centroid).dot(normal))

    metrics = {
        "num_points": int(points3d.shape[0]),
        "centroid": centroid.tolist(),
        "plane_normal": normal.tolist(),
        "fitted_center_3d": center3d.tolist(),
        "radius": float(R),
        "residuals": residuals.tolist(),
        "residuals_rms": float(np.sqrt(np.mean(residuals ** 2))),
        "residuals_max": float(np.max(residuals)),
        "coplanar_max": float(np.max(coplanar_dists)),
        "coplanar_rms": float(np.sqrt(np.mean(coplanar_dists ** 2))),
    }

    # decide thresholds relative to radius
    R_ref = max(1e-6, R)
    tol_plane = max(0.05 * R_ref, 0.1)  # max distance to plane allowed
    tol_rms = max(0.02 * R_ref, 0.05)   # RMS residual allowed
    tol_max = max(0.05 * R_ref, 0.1)    # max residual allowed

    pass_plane = metrics["coplanar_max"] <= tol_plane
    pass_rms = metrics["residuals_rms"] <= tol_rms
    pass_max = metrics["residuals_max"] <= tol_max

    verdict = pass_plane and pass_rms and pass_max

    if verbose:
        print("Circle fit results:")
        if data and data.get("description"):
            print(f"  Description: {data.get('description')}")
        print(f"  Num points: {metrics['num_points']}")
        print(f"  Fitted center (3D): {metrics['fitted_center_3d']}")
        print(f"  Radius: {metrics['radius']:.4f}")
        print(f"  Residuals RMS: {metrics['residuals_rms']:.4f}   Max: {metrics['residuals_max']:.4f}")
        print(f"  Coplanarity max: {metrics['coplanar_max']:.4f}   RMS: {metrics['coplanar_rms']:.4f}")
        print("\nThresholds used:")
        print(f"  tol_plane = {tol_plane:.4f} (max allowed distance from plane)")
        print(f"  tol_rms = {tol_rms:.4f} (RMS residual allowed)")
        print(f"  tol_max = {tol_max:.4f} (max residual allowed)")
        print("\nVerdict: {}".format("PASS (points form an approximate circle)" if verdict else "FAIL (points do not form a circle)"))

    return verdict, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.path.join("outputs", "goals_10_20260111_231944.json"),
                        help="Path to goals JSON file")

    args = parser.parse_args()

    pts, data = load_goals(args.path)
    if pts.size == 0:
        print("No points found in JSON 'goals_ned'")
        return 2

    verdict, metrics = evaluate(pts, data)
    # optionally save metrics next to file
    out_path = os.path.splitext(args.path)[0] + "_circle_check.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"verdict": bool(verdict), "metrics": metrics}, f, indent=2, ensure_ascii=False)
        print(f"Saved results to {out_path}")
    except Exception as e:
        print(f"Could not save results: {e}")

    return 0


if __name__ == "__main__":
    main()
