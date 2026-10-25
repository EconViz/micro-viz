"""Sweep a figure's parameter and save the result as an Animated SVG or a GIF."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mosaickit import Canvas, TextLayer

from micro_viz.animation.depict import Depictor, warn_skipped
from micro_viz.animation.stage import POINTS_PER_INCH, Stage

if TYPE_CHECKING:
    from kinetickit.animation import Animation

Frames = Callable[[float], Canvas]
"""Builds the canvas of one value of the swept parameter, with the figure's own builder."""

INSTALL_HINT = "Install it with:  pip install 'micro-viz[animation]'"
TITLE_ID = "micro.title"
TITLE_GAP_PT = 14.0
"""Height in points of a figure title above the plot area."""


def _require_kinetickit() -> None:
    try:
        import kinetickit  # noqa: F401
    except ImportError as error:
        raise ImportError(f"KineticKit is required to animate figures.\n{INSTALL_HINT}") from error


def canvases_for(factory: Frames, values: Sequence[float]) -> list[Canvas]:
    """The canvas of every value, built by ``factory``; the axes must not change between them."""
    if not values:
        raise ValueError("values must not be empty")
    canvases = [factory(float(value)) for value in values]
    first = canvases[0].spec
    for canvas in canvases[1:]:
        spec = canvas.spec
        if (spec.x_range, spec.y_range, spec.width, spec.height) != (
            first.x_range,
            first.y_range,
            first.width,
            first.height,
        ):
            raise ValueError(
                "the axis ranges and size must be the same for every value; "
                "pass x_max=, y_range= and size= to the builder"
            )
    return canvases


def _layers(depictor: Depictor, canvas: Canvas) -> list[Any]:
    layers = depictor.layers(canvas)
    title = canvas.spec.title
    if title:
        x0, x1 = canvas.spec.x_range
        layers.append(
            TextLayer(
                ((x0 + x1) / 2, canvas.spec.y_range[1]),
                title,
                id=TITLE_ID,
                role="title",
                anchor="bottom",
                offset=(0.0, TITLE_GAP_PT),
                z_index=9,
            )
        )
    return layers


def animation_from_canvases(
    canvases: Sequence[Canvas],
    *,
    stage: Stage | None = None,
    seconds_per_step: float | None = None,
) -> tuple[Animation, Depictor]:
    """A kinetickit animation moving through ``canvases`` in order, with the depictor used."""
    _require_kinetickit()
    from kinetickit import Animation
    from kinetickit.adapters import transition
    from kinetickit.geometry.two_d import Bounds2D, Vec2

    selected = stage or Stage()
    depictor = Depictor(canvases[0], selected)
    layer_lists = [_layers(depictor, canvas) for canvas in canvases]
    duration = seconds_per_step if seconds_per_step is not None else selected.seconds_per_step
    if len(layer_lists) == 1:
        layer_lists = [layer_lists[0], layer_lists[0]]
    steps = [
        transition(before, after, depictor.depict, duration=duration)
        for before, after in zip(layer_lists, layer_lists[1:], strict=False)
    ]
    motion = steps[0].motion
    for step in steps[1:]:
        motion = motion.then(step.motion)
    scene = steps[0].scene
    scene = scene.bind(
        {scene.camera.ref("view"): Bounds2D(Vec2(0.0, 0.0), Vec2(depictor.width, depictor.height))}
    )
    return Animation(scene, motion), depictor


def save_svg(
    factory: Frames,
    values: Sequence[float],
    path: str | Path,
    *,
    stage: Stage | None = None,
    seconds_per_step: float | None = None,
    background: str | None = None,
    loop: bool = True,
    title: str | None = None,
    description: str | None = None,
) -> Path:
    """Save a native Animated SVG of ``factory`` swept over ``values``; returns the path."""
    _require_kinetickit()
    from kinetickit.geometry.two_d import Bounds2D, Vec2
    from kinetickit.layout import LayoutResult, Margins, Viewport

    canvases = canvases_for(factory, values)
    selected = stage or Stage()
    animation, depictor = animation_from_canvases(
        canvases, stage=selected, seconds_per_step=seconds_per_step
    )
    spec = canvases[0].spec
    width = spec.width * POINTS_PER_INCH
    height = spec.height * POINTS_PER_INCH
    margins = Margins(
        top=selected.top, right=selected.right, bottom=selected.bottom, left=selected.left
    )
    layout = LayoutResult(
        Viewport(width, height, margins),
        Bounds2D(Vec2(0.0, 0.0), Vec2(depictor.width, depictor.height)),
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    quiet = logging.getLogger("fontTools")
    previous = quiet.level
    quiet.setLevel(logging.ERROR)
    animation.save(
        target,
        renderer="vector",
        width=width,
        height=height,
        margins=margins,
        layout=layout,
        background=background,
        embed_fonts=False,
        loop=loop,
        title=title,
        description=description,
    )
    quiet.setLevel(previous)
    warn_skipped(depictor)
    return target


def _interpolate(values: Sequence[float], per_step: int) -> list[float]:
    if len(values) == 1 or per_step <= 1:
        return [float(value) for value in values]
    result: list[float] = []
    for low, high in zip(values, values[1:], strict=False):
        result.extend(low + (high - low) * index / per_step for index in range(per_step))
    result.append(float(values[-1]))
    return result


def _png_frames(
    factory: Frames, values: Sequence[float], stem: str, dpi: int | None
) -> Iterator[bytes]:
    with tempfile.TemporaryDirectory(prefix="micro-viz-animation-") as directory:
        for index, value in enumerate(values):
            canvas = factory(float(value))
            if dpi is not None:
                canvas.spec = canvas.spec.replace(dpi=dpi)
            # Named after the animation so [figure.<stem>.label."<id>"] moves labels per frame.
            target = Path(directory) / f"{index:06d}" / f"{stem}.png"
            target.parent.mkdir(parents=True)
            canvas.save(target)
            yield target.read_bytes()


def save_gif(
    factory: Frames,
    values: Sequence[float],
    path: str | Path,
    *,
    frames_per_step: int = 12,
    fps: int = 15,
    dpi: int | None = None,
    loop: int = 0,
) -> Path:
    """Save a GIF of mosaickit-rendered frames of ``factory`` swept over ``values``.

    Every frame is a full mosaickit render, so labels are placed exactly as in the static
    figure; ``frames_per_step`` frames are drawn between two values (linear steps).
    """
    _require_kinetickit()
    try:
        from kinetickit.exporters import export_png_frames
    except ImportError as error:  # pragma: no cover - the extra installs it
        raise ImportError(f"GIF export needs kinetickit[raster].\n{INSTALL_HINT}") from error
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    swept = _interpolate(values, frames_per_step)
    export_png_frames(
        _png_frames(factory, swept, target.stem, dpi), target, fps=fps, loop=loop, disposal=2
    )
    return target
