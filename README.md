# micro-viz

`micro-viz` is the EconViz package for producer theory, costs, firm behaviour,
market structure, nonlinear pricing, factor demand, uncertainty, and information
economics. Version `1.0.0b1` is the first public beta. It covers
production and costs, competition, monopoly and pricing, oligopoly, inputs and factor
markets, and uncertainty and information, with 135 example figures. Documentation, with
every figure and its script, is at <https://econ-viz.org/micro-viz/>.

## Boundaries

- `micro-viz` owns firm-side and market-structure analysis.
- [`utility-viz`](https://github.com/EconViz/utility-viz) owns consumer theory and
  general equilibrium.
- [`principle-viz`](https://github.com/EconViz/principle-viz) owns introductory
  demand-and-supply policy diagrams, externalities, and public goods.
- Game theory is outside this package.
- [`mosaickit`](https://github.com/EconViz/mosaickit) owns scenes, layers, themes,
  layout, and rendering backends.

Domain models and solvers must remain renderer-neutral. Visual builders compile typed
economic results into public MosaicKit layers, and only MosaicKit talks to a backend.

## Object-oriented API

Use `Firm` when several firm-side models belong together. Topic packages use plural chapter
names such as `costs`, while model classes use singular names such as `Cost`.

```python
from micro_viz import Firm
from micro_viz.firm import Cost, ProductionFunction

cost = Cost("TC = 10 + Q^2")
production = ProductionFunction(linear=6, quadratic=3, cubic=-0.5)
firm = Firm(cost=cost, production=production)

firm.total_cost(2)  # 14
firm.marginal_cost(2)  # 4
firm.profit(2, price=8)  # 2
```

`ProductionFunction.from_callable(lambda labor: ...)` accepts a continuous Python function.
`ProductionFunction.from_table(labor=[...], output=[...])` accepts a production schedule and
uses straight segments between observations, so TP, AP, and interval MP can be drawn together.

The `firm` domain contains only `production`, `costs`, `perfect_competition`, `monopoly`,
`monopolistic_competition`, and `oligopoly`. Long-run cost belongs to `costs`; isoquants and
isocost analysis belong to `production`; entry and pricing strategies live with the market
structure that uses them.

### Dependency boundary

`micro-viz` depends only on MosaicKit (`mosaickit>=1.0.0rc16,<2.0.0`); GlyphKit stays
MosaicKit's transitive text layer. BezierKit becomes a direct dependency only when a figure
consumes its public geometry API. KineticKit is optional: the `animation` extra adds
`kinetickit[raster]`, and static figures never import it.

## Short-run production

`ShortRunProductionFunction` uses the textbook cubic equation
`Q(L) = aL + bL^2 + cL^3`, with `a >= 0`, `b > 0`, and `c < 0`. The analysis reports
sampled total, average, and marginal products plus exact boundaries for increasing,
diminishing, and negative marginal returns.

```python
from micro_viz import (
    ShortRunProductionFunction,
    analyze_production,
    average_marginal_product_canvas,
    total_product_canvas,
)

production = ShortRunProductionFunction(linear=6, quadratic=3, cubic=-0.5)
result = analyze_production(production, input_range=(0, 6))

total_product_canvas(result).save("total-product.svg")  # no title unless title= is given
average_marginal_product_canvas(result, title="Short-run products").save("products.svg")
```

Both figures mark the three boundary inputs with dashed drop lines: the maximum of MP
(`L_1`), the maximum of AP where AP = MP (`L_2`) and the maximum of TP where MP = 0 (`L_3`).
The increasing, diminishing and negative marginal-return regions are shaded and named under
the horizontal axis.

The returned `ProductionAnalysis` is renderer-neutral and `to_dict()` includes the equation,
coefficient sign convention, sampled values, and return-region boundaries. Visual layers use
stable `micro.production.*` IDs and roles.

## Short-run costs

Write the cost the way a textbook does and draw it in one step:

```python
from micro_viz import Cost, cost_curves

cost = Cost("TC = 200 + 120Q - 18Q^2 + Q^3")
cost_curves(cost, output=(1, 16)).save("unit_cost.svg")  # MC, ATC, AVC, AFC and the two minima
```

`Cost` also takes `Cost("VC = 120Q - 18Q^2 + Q^3", fixed=200)`, `Cost("MC = 120 - 36Q + 3Q^2",
fixed=200)`, `Cost("ATC = 200/Q + 120 - 18Q + Q^2")`, `Cost.polynomial(200, 120, -18, 1)`
(ascending coefficients) and `Cost.from_table(q=[0, 1, 2], tc=[10, 18, 24])`. The formula is read
by a small parser of our own (numbers, `Q` or `q`, `+ - * / ^`, brackets, `exp`, `ln`, `sqrt`,
and `36Q` or `2(Q+1)` for products); nothing is evaluated as Python, and a mistake gives a short
message with a caret, in the figure language. `Cost` knows `.fc`, `.tc(q)`, `.vc(q)`, `.mc(q)`,
`.atc(q)`, `.avc(q)`, `.afc(q)`, `.min_avc()`, `.min_atc()`, `.shutdown_price()` and
`.breakeven_price()`; the minima are closed-form where the algebra allows and found to machine
precision otherwise. It refuses a negative fixed cost and a marginal cost that is not positive on
the plotted output range, naming the interval. `cost_curves(..., show=("MC", "AVC"), marks=False)`
chooses the curves and the marks; `total_cost_canvas`, `unit_cost_canvas`, `cost_curves_panels`
and `cost_curves_grid` accept a `Cost` (or a formula) and `output_range=(low, high)` directly.

The advanced models stay. `CubicCost` is the textbook `TC(q) = FC + bq + cq^2 + dq^3` (`b, d > 0`,
`c < 0` for the U-shape; a cubic `Cost` uses it internally and gives the same numbers).
`PiecewiseCost` is defined by its marginal cost, built from `CostSegment`s that may jump where an
extra shift or processing unit starts, with a capacity. `analyze_costs` samples every measure
(TFC, TVC, TC, AFC, AVC, ATC, MC) and reports the exact minimum points: MC crosses AVC and ATC at
their minima.

```python
from micro_viz import (
    CostSegment,
    CubicCost,
    PiecewiseCost,
    analyze_costs,
    cost_curves_grid,
    piecewise_cost_canvas,
    unit_cost_canvas,
)

cost = CubicCost(fixed_cost=200, linear=120, quadratic=-18, cubic=1)
analysis = analyze_costs(cost, output_range=(1, 16))
cost_curves_grid(analysis).save("costs.svg")  # totals above unit costs
unit_cost_canvas(analysis, curves=("mc", "avc")).save("u.svg")  # a subset of the curves

steps = PiecewiseCost((CostSegment(6, 11.4), CostSegment(9, 13.0)))
piecewise_cost_canvas(analyze_costs(steps, output_range=(0, 9)), prices=(12.2, 14)).save("s.svg")
```

`unit_cost_canvas(analysis, output=q)` marks the unit costs at one output, so the figure can be
swept as output grows (see `examples/scripts/animation/animate_costs.py`); `PiecewiseCost.output_at_price`
gives the output a price band selects.

## Install

`micro-viz` requires Python 3.10 or later.

Install the beta from PyPI. MosaicKit 1.0.0rc16 is a pre-release, so allow pre-releases
until its 1.0 release is published.

```bash
uv add --prerelease allow micro-viz==1.0.0b1
```

For a source checkout:

```bash
git clone https://github.com/EconViz/micro-viz.git
cd micro-viz
uv sync --frozen
```

## Shared settings

Every EconViz diagram package reads the same `econ-viz.toml`. `micro-viz` declares its
configuration schema to MosaicKit and does not parse TOML itself. With no settings file,
figures use the same colour `default` theme as `principle-viz`, always on a white background.
Manuals, documentation, and bundled examples explicitly select the black-and-white `manual`
theme. Shared settings such as `base`, fonts,
axis and label colours, and per-figure label nudges work across installed EconViz packages.

```toml
base = "manual"

[font]
text = "serif"

[color]
axis = "#1a1a1a"
label = "#1a1a1a"
```

micro-viz's own options live below `[micro.*]`; unknown settings are rejected instead of
being silently ignored.

```toml
[micro]
language = "zh-TW"        # built-in figure text: en, zh-TW or zh-CN

[micro.color]             # any element of micro_viz.core.theme.ELEMENT_ROLES
marginal = "#1a1a1a"

[micro.stroke]            # widths in points
curve = 3.5
guide = 1.0

[micro.opacity]
region = 0.2              # opacity of shaded regions

[micro.label.curve]       # move whole groups of labels: point, curve, region, mark, annotation
top = "2pt"
```

Single labels of single figures are moved with `[figure.<file>.label."<layer id>"]`. Shaded
regions are set with `[micro.region]` (`fill`, `extent`). A dashed guide that lies on a solid
straight curve is dropped by every builder (`drop_covered_guides`); its mark stays.

## Animation

A figure about a shift, a sweep or an adjustment animates through the same canvas builder that
draws it. Install the optional extra (`pip install "micro-viz[animation]"`, which adds
`kinetickit[raster]`); static figures never import kinetickit and work without it.

```python
from micro_viz.animation import save_gif, save_svg


def frame(linear: float):  # the figure's own builder for one parameter value
    function = ShortRunProductionFunction(linear=linear, quadratic=3, cubic=-0.5)
    result = analyze_production(function, input_range=(0, 6))
    return average_marginal_product_canvas(result, y_range=(-25, 25), x_max=6.6)


save_svg(frame, [4, 6, 8], "products.svg")  # native Animated SVG, curves morph
save_gif(frame, [4, 6, 8], "products.gif", fps=15)  # mosaickit-rendered frames
```

mosaickit draws every frame; kinetickit moves between frames and matches layers by their stable
ids. The axes and size must be fixed across values (pass `x_max=`, `y_range=` and `size=`). The
animated SVG places text from the layers' anchors (no automatic collision avoidance); the GIF
uses mosaickit's placement exactly. See `examples/scripts/animation/animate_production.py`.

## Nothing is hard-coded

Figure titles, axis names, curve and region names, ranges, sample counts, sizes, colours, line
widths and fonts are arguments or settings, never constants inside a model or a builder.
Built-in text lives in `src/micro_viz/locale/labels.json`, keyed by stable ids and then by
language (`en`, `zh-TW`, `zh-CN`); a builder takes `title=`, `x_label=`, `y_label=` and
`labels={id: text}` to replace any of it. Tests change a parameter and check that the figure
follows, and scan the source for colour literals, font names and absolute paths.

## Examples

The scripts live in `examples/scripts/<topic>/` (production, costs, competition,
monopoly, oligopoly, factor markets, uncertainty, information and more). They use the
black-and-white `manual` look (`examples/econ-viz.toml`: TeX Gyre Pagella text and math, white
background); `econ-viz.zh-TW.toml` and `econ-viz.zh-CN.toml` draw the Chinese editions. Generated
SVG files go to `examples/output/<topic>/` (one folder per topic, e.g. `pricing/`, `costs/`, named like the script's folder) and are ignored by Git.

```bash
uv run python examples/scripts/production/production.py
uv run python examples/scripts/production/production.py --cubic -0.4 --max-input 8 --title "Own title"
uv run python examples/scripts/production/production.py --config examples/econ-viz.zh-TW.toml \
    --fonts-dir path/to/NotoSerifTC
```

Every example takes `--output-dir` (used as given; default is its topic folder), `--config` (an `econ-viz.toml`), `--fonts-dir` (where the
font files named by the settings live; TeX Gyre fonts are found through `kpsewhich`) and the
economic parameters of its model. Figures carry no title unless `--title` is given.

## Development

```bash
uv run ruff check src tests examples/scripts
uv run ruff format --check src tests examples/scripts
uv run mypy
uv run pytest
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture and pull-request conventions.
