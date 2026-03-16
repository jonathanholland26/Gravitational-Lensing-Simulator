"""
Gravitational Lensing Simulator

Simulates the bending of light around a massive object using the
gravitational lens equation from General Relativity. Produces Einstein
rings, arcs, and quad images with real-time interactive controls.

Author  : Jonathan Holland
Created : March 2026
License: MIT
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation, PillowWriter

def make_grid(size=500):
    """
    Create a 2D normalised coordinate grid for the image plane.

    Coordinates are expressed in units of the Einstein radius, so the
    Einstein ring lies at radius 1.0 from the origin.

    Parameters
    ----------
    size : int, optional
        Number of pixels along each axis. Default is 500.

    Returns
    -------
    X : np.ndarray, shape (size, size)
        x-coordinates of each pixel in the image plane.
    Y : np.ndarray, shape (size, size)
        y-coordinates of each pixel in the image plane.
    """
    coords = np.linspace(-2, 2, size)
    X, Y = np.meshgrid(coords, coords)
    return X, Y


def deflect(X, Y, theta_E):
    """
    Compute the deflected source plane coordinates for each image pixel.

    Applies the gravitational lens equation in 2D, mapping every point
    in the image plane back to its corresponding position in the source
    plane. The deflection is strongest near the lens center and falls
    off with distance.

    Parameters
    ----------
    X : np.ndarray, shape (size, size)
        x-coordinates of each pixel in the image plane.
    Y : np.ndarray, shape (size, size)
        y-coordinates of each pixel in the image plane.
    theta_E : float
        Einstein radius in normalised units. Controls the strength
        of the lens — larger values correspond to a more massive lens.

    Returns
    -------
    X_src : np.ndarray, shape (size, size)
        Deflected x-coordinates in the source plane.
    Y_src : np.ndarray, shape (size, size)
        Deflected y-coordinates in the source plane.
    """
    R_squared = X ** 2 + Y ** 2
    R_squared = np.clip(R_squared, 1e-10, None)  # prevent division by zero at lens center
    X_src = X - theta_E ** 2 * (X / R_squared)
    Y_src = Y - theta_E ** 2 * (Y / R_squared)
    return X_src, Y_src


def make_source(X_src, Y_src, x0, y0, sigma):
    """
    Generate a 2D Gaussian brightness distribution in the source plane.

    Models a background source as a circular Gaussian blob. Evaluating
    this on deflected coordinates produces the gravitational lensing
    distortion effect.

    Parameters
    ----------
    X_src : np.ndarray, shape (size, size)
        x-coordinates of the source plane, output from deflect().
    Y_src : np.ndarray, shape (size, size)
        y-coordinates of the source plane, output from deflect().
    x0 : float
        x-coordinate of the source centre in units of Einstein radii.
    y0 : float
        y-coordinate of the source centre in units of Einstein radii.
    sigma : float
        Width of the Gaussian blob in units of Einstein radii.
        Smaller values produce a more compact, point-like source.

    Returns
    -------
    brightness : np.ndarray, shape (size, size)
        Brightness value at each pixel, normalised between 0 and 1.
    """
    return np.exp(-((X_src - x0) ** 2 + (Y_src - y0) ** 2) / (2 * sigma ** 2))


def pixel_coords(X_src, Y_src, size=500, extent=2):
    """
    Convert source plane coordinates from Einstein radius units to pixel indices.

    map_coordinates requires pixel indices rather than normalised coordinates,
    so this function converts the deflected source plane positions into the
    corresponding pixel locations in the source image array.

    Parameters
    ----------
    X_src : np.ndarray, shape (size, size)
        Deflected x-coordinates in the source plane, in units of Einstein radii.
    Y_src : np.ndarray, shape (size, size)
        Deflected y-coordinates in the source plane, in units of Einstein radii.
    size : int, optional
        Number of pixels along each axis. Default is 500.
    extent : float, optional
        Half-width of the coordinate grid in Einstein radii. Default is 2.

    Returns
    -------
    X_pixel : np.ndarray, shape (size, size)
        x pixel indices corresponding to the deflected source positions.
    Y_pixel : np.ndarray, shape (size, size)
        y pixel indices corresponding to the deflected source positions.
    """
    X_pixel = (X_src + extent) * (size / (2 * extent))
    Y_pixel = (Y_src + extent) * (size / (2 * extent))
    return X_pixel, Y_pixel


def render(source, X_pixel, Y_pixel, order=3):
    """
    Sample the source image at deflected pixel coordinates via interpolation.

    Uses scipy's map_coordinates to perform bicubic interpolation of the
    source brightness array at arbitrary pixel positions produced by the
    gravitational deflection. This is the step that produces the visible
    lensing distortion.

    Parameters
    ----------
    source : np.ndarray, shape (size, size)
        Undistorted source brightness array from make_source().
    X_pixel : np.ndarray, shape (size, size)
        x pixel indices to sample, from pixel_coords().
    Y_pixel : np.ndarray, shape (size, size)
        y pixel indices to sample, from pixel_coords().
    order : int, optional
        Interpolation order. 3 = bicubic (default, higher quality),
        1 = bilinear (faster, use during animation testing).

    Returns
    -------
    image : np.ndarray, shape (size, size)
        Final rendered image with gravitational lensing distortion applied.
    """
    return map_coordinates(source, [Y_pixel, X_pixel], order=order)


def update(X, Y, theta_E, x0, y0, sigma):
    """
    Recompute the lensed image for given lens and source parameters.

    Parameters
    ----------
    X : np.ndarray, shape (size, size)
        x-coordinates of the image plane grid.
    Y : np.ndarray, shape (size, size)
        y-coordinates of the image plane grid.
    theta_E : float
        Einstein radius in normalised units.
    x0 : float
        x-coordinate of the source centre in units of Einstein radii.
    y0 : float
        y-coordinate of the source centre in units of Einstein radii.

    Returns
    -------
    image : np.ndarray, shape (size, size)
        The newly rendered lensed image.
    """
    X_src, Y_src = deflect(X, Y, theta_E)
    source = make_source(X, Y, x0, y0, sigma)
    X_pixel, Y_pixel = pixel_coords(X_src, Y_src)
    return render(source, X_pixel, Y_pixel)

if __name__ == "__main__":

    X, Y = make_grid()

    fig = plt.figure(figsize=(6, 8))
    ax_image = fig.add_axes([0.1, 0.35, 0.8, 0.6])
    ax_theta = fig.add_axes([0.2, 0.22, 0.6, 0.03])
    ax_X_src = fig.add_axes([0.2, 0.16, 0.6, 0.03])
    ax_Y_src = fig.add_axes([0.2, 0.10, 0.6, 0.03])
    ax_sigma = fig.add_axes([0.2, 0.04, 0.6, 0.03])

    slider_theta = Slider(ax_theta, "Theta_E", 0.1, 2.0, valinit=0.5)
    slider_x = Slider(ax_X_src, "X source", -1.5, 1.5, valinit=0.0)
    slider_y = Slider(ax_Y_src, "Y source", -1.5, 1.5, valinit=0.0)
    slider_sigma = Slider(ax_sigma, "Sigma", 0.01, 0.5, valinit = 0.05)

    im = ax_image.imshow(
        update(X, Y, 0.5, 0.0, 0.0, 0.05),
        cmap='gray',
        origin='lower',
        vmin=0,
        vmax=1
    )

    ax_image.plot(250, 250, '+w', markersize=6, markeredgewidth=1.5)

    ax_image.set_title("θ_E = 0.50   x₀ = 0.00   y₀ = 0.00   σ = 0.050")

    def update_image(val):
        new_image = update(X, Y, slider_theta.val, slider_x.val, slider_y.val, slider_sigma.val)
        im.set_data(new_image)
        ax_image.set_title(f"θ_E = {slider_theta.val:.3f}   x₀ = {slider_x.val:.3f}   y₀ = {slider_y.val:.3f}   ç {slider_sigma.val:.3f}")

    slider_theta.on_changed(update_image)
    slider_x.on_changed(update_image)
    slider_y.on_changed(update_image)
    slider_sigma.on_changed(update_image)


    fig_anim = plt.figure(figsize = (6, 8))
    ax_anim = fig_anim.add_axes([0.1, 0.1, 0.8, 0.8])

    im_anim = ax_anim.imshow(
        update(X, Y, 0.5, 0.0, 0.0, 0.05),
        cmap='gray',
        origin='lower',
        vmin=0,
        vmax=1
    )
    ax_anim.plot(250, 250, '+w', markersize=6, markeredgewidth=1.5)

    x_positions = np.linspace(-1.5, 1.5, 200)

    def animate(frame):
        x0 = x_positions[frame]
        new_image = update(X, Y, slider_theta.val, x0, 0.0, slider_sigma.val)
        im_anim.set_data(new_image)
        ax_anim.set_title(f"θ_E = {slider_theta.val:.3f}   x₀ = {x0:.3f}   y₀ = 0.0   σ = {slider_sigma.val:.3f}")
        return [im_anim]

    anim = FuncAnimation(fig_anim, animate, frames=200, interval=50)

    # save static Einstein ring screenshot
    fig.savefig('einstein_ring.png', dpi=150, bbox_inches='tight')

    # save animation as gif
    writer = PillowWriter(fps=20)
    anim.save('animation.gif', writer=writer)