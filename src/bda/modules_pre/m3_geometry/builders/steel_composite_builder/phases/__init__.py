"""Build phases of the steel-composite grillage pipeline.

Each phase module exposes ``run(ctx)`` orchestrating its internal sub-steps.
The builder executes the phases in a fixed order.
"""
