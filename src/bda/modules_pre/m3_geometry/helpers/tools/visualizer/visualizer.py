from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from bda.domain.models.analytical_multi_model import AnalyticalMultiModel
from bda.domain.models.submodels.element import Element1D
from bda.domain.models.submodels.element import ElementLink
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.node import Node


class GeometryVisualizer:
	"""Render FE geometry from one or more GeometryGroup objects or AnalyticalMultiModel."""

	@staticmethod
	def plot(
		source: GeometryGroup | AnalyticalMultiModel | Iterable[GeometryGroup],
		flat: bool = True,
		include_links: bool = False,
		include_reference_elements: bool = False,
		include_finite_elements: bool = True,
		show_nodes: bool = True,
		save_to_file: bool = True,
		file_name: str | None = None,
		file_format: str = "png",
		dpi: int = 200,
		show: bool = True,
		interactive: bool = True,
		isometric: bool = False,
		elev: float = 30.0,
		azim: float = -60.0,
		node_size: float = 12.0,
		element_width: float = 1.0,
		title: str | None = None,
	):
		"""
		Plot model geometry using matplotlib.

		Args:
			source: Root GeometryGroup, AnalyticalMultiModel, or collection of GeometryGroup objects.
			flat: If True, plots in XY plane. If False, plots in 3D.
			include_links: Include analytical links in rendering as dotted lines.
			include_reference_elements: Include reference elements in rendering.
			include_finite_elements: Include finite elements in rendering.
			show_nodes: Show node markers.
			save_to_file: Save rendered figure to an image file.
			file_name: Output file name. If None, uses geometry_xy/geometry_3d.
			file_format: Image format used by matplotlib savefig.
			dpi: Saved image DPI.
			show: Call matplotlib show at the end.
			interactive: Enable interactive mode (`plt.ion`) for rotatable 3D view.
			isometric: Applies a standard isometric camera angle for 3D view. Cannot be used with flat=True.
			elev: Elevation camera angle for 3D.
			azim: Azimuth camera angle for 3D.
			node_size: Node marker size.
			element_width: Width of element lines.
			title: Optional custom plot title.

		Returns:
			Tuple[Figure, Axes]: matplotlib figure and axis objects.
		"""
		try:
			import matplotlib.pyplot as plt
		except ModuleNotFoundError as exc:
			raise ModuleNotFoundError(
				"matplotlib is required for geometry visualization. Install it with: pip install .[test]"
			) from exc

		if flat and isometric:
			raise ValueError("`isometric=True` requires `flat=False` (isometric applies only to 3D view).")
		if not include_reference_elements and not include_finite_elements and not include_links:
			raise ValueError("At least one geometry type must be included for plotting.")

		root_groups = GeometryVisualizer._resolve_geometry_groups(source)
		nodes, grouped_elements = GeometryVisualizer._collect_nodes_and_elements(
			root_groups,
			include_links=include_links,
			include_reference_elements=include_reference_elements,
			include_finite_elements=include_finite_elements,
		)

		if interactive:
			plt.ion()

		fig = plt.figure(figsize=(15, 15))
		ax = fig.add_subplot(111, projection=None if flat else "3d")

		reference_style = "--" if include_reference_elements and include_finite_elements else "-"

		# Draw finite elements first, then reference elements so dotted reference lines stay visible on top.
		for group_index, (_, finite_elements, _, _) in enumerate(grouped_elements):
			group_color = GeometryVisualizer._get_group_color(group_index)
			for element in finite_elements:
				x = [GeometryVisualizer._to_meter_value(element.node_start.X), GeometryVisualizer._to_meter_value(element.node_end.X)]
				y = [GeometryVisualizer._to_meter_value(element.node_start.Y), GeometryVisualizer._to_meter_value(element.node_end.Y)]
				if flat:
					ax.plot(x, y, color=group_color, linewidth=element_width, linestyle="-", zorder=2)
				else:
					z = [GeometryVisualizer._to_meter_value(element.node_start.Z), GeometryVisualizer._to_meter_value(element.node_end.Z)]
					ax.plot(x, y, z, color=group_color, linewidth=element_width, linestyle="-", zorder=2)

		for group_index, (_, _, _, links) in enumerate(grouped_elements):
			group_color = GeometryVisualizer._get_group_color(group_index)
			for element in links:
				x = [GeometryVisualizer._to_meter_value(element.node_start.X), GeometryVisualizer._to_meter_value(element.node_end.X)]
				y = [GeometryVisualizer._to_meter_value(element.node_start.Y), GeometryVisualizer._to_meter_value(element.node_end.Y)]
				if flat:
					ax.plot(x, y, color=group_color, linewidth=element_width, linestyle=":", zorder=2.5)
				else:
					z = [GeometryVisualizer._to_meter_value(element.node_start.Z), GeometryVisualizer._to_meter_value(element.node_end.Z)]
					ax.plot(x, y, z, color=group_color, linewidth=element_width, linestyle=":", zorder=2.5)

		for group_index, (_, _, reference_elements, _) in enumerate(grouped_elements):
			group_color = GeometryVisualizer._get_group_color(group_index)
			for element in reference_elements:
				x = [GeometryVisualizer._to_meter_value(element.node_start.X), GeometryVisualizer._to_meter_value(element.node_end.X)]
				y = [GeometryVisualizer._to_meter_value(element.node_start.Y), GeometryVisualizer._to_meter_value(element.node_end.Y)]
				if flat:
					ax.plot(x, y, color=group_color, linewidth=element_width, linestyle=reference_style, zorder=3)
				else:
					z = [GeometryVisualizer._to_meter_value(element.node_start.Z), GeometryVisualizer._to_meter_value(element.node_end.Z)]
					ax.plot(x, y, z, color=group_color, linewidth=element_width, linestyle=reference_style, zorder=3)

		if show_nodes and nodes:
			x = [GeometryVisualizer._to_meter_value(node.X) for node in nodes]
			y = [GeometryVisualizer._to_meter_value(node.Y) for node in nodes]
			if flat:
				ax.scatter(x, y, s=node_size, color="tab:red", alpha=0.9)
			else:
				z = [GeometryVisualizer._to_meter_value(node.Z) for node in nodes]
				ax.scatter(x, y, z, s=node_size, color="tab:red", alpha=0.9)

		if flat:
			ax.set_xlabel("X [m]")
			ax.set_ylabel("Y [m]")
			ax.set_aspect("equal", adjustable="box")
		else:
			ax.set_xlabel("X [m]")
			ax.set_ylabel("Y [m]")
			ax.set_zlabel("Z [m]")
			if isometric:
				ax.view_init(elev=35.264, azim=45)
			else:
				ax.view_init(elev=elev, azim=azim)
			GeometryVisualizer._set_equal_3d_axes(ax, nodes)

		ax.set_title(title or ("Geometry view (XY)" if flat else "Geometry view (3D)"))
		ax.grid(True, alpha=0.3)

		if save_to_file:
			output_path = GeometryVisualizer._build_output_path(flat=flat, file_name=file_name, file_format=file_format)
			fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

		if show:
			plt.show(block=not interactive)

			if interactive:
				while plt.fignum_exists(fig.number):
					plt.pause(0.1)

		return fig, ax

	@staticmethod
	def _resolve_geometry_groups(
		source: GeometryGroup | AnalyticalMultiModel | Iterable[GeometryGroup],
	) -> list[GeometryGroup]:
		if isinstance(source, GeometryGroup):
			return [source]

		if isinstance(source, AnalyticalMultiModel):
			if source.geometry_group is None:
				raise ValueError("AnalyticalMultiModel does not have assigned geometry_group.")

			return [source.geometry_group]

		if isinstance(source, Iterable):
			groups = list(source)
			if not groups:
				raise ValueError("Geometry group collection is empty.")

			if any(not isinstance(group, GeometryGroup) for group in groups):
				raise TypeError("All entries in source collection must be GeometryGroup instances.")

			return groups

		raise TypeError("Source must be GeometryGroup, AnalyticalMultiModel, or iterable of GeometryGroup.")

	@staticmethod
	def _collect_nodes_and_elements(
		root_groups: Iterable[GeometryGroup],
		*,
		include_links: bool,
		include_reference_elements: bool,
		include_finite_elements: bool,
	) -> tuple[list[Node], list[tuple[GeometryGroup, list[Element1D], list[Element1D], list[ElementLink]]]]:
		node_map: dict[int, Node] = {}
		seen_group_ids: set[int] = set()
		grouped_elements: list[tuple[GeometryGroup, list[Element1D], list[Element1D], list[ElementLink]]] = []

		for root_group in root_groups:
			for group in root_group.iter_groups():
				group_identity = id(group)
				if group_identity in seen_group_ids:
					continue
				seen_group_ids.add(group_identity)

				finite_elements: list[Element1D] = []
				reference_elements: list[Element1D] = []
				links: list[ElementLink] = []

				if include_finite_elements:

					for element in group.analytical_typology.elements:
						if not isinstance(element, Element1D):
							continue

						finite_elements.append(element)
						node_map[id(element.node_start)] = element.node_start
						node_map[id(element.node_end)] = element.node_end

				if include_reference_elements:
					for node in group.reference_nodes:
						node_map[id(node)] = node

					for element in group.reference_elements:
						if not isinstance(element, Element1D):
							continue

						reference_elements.append(element)
						node_map[id(element.node_start)] = element.node_start
						node_map[id(element.node_end)] = element.node_end

				if include_links:
					for element in group.analytical_typology.links:
						links.append(element)
						node_map[id(element.node_start)] = element.node_start
						node_map[id(element.node_end)] = element.node_end

				if finite_elements or reference_elements or links:
					grouped_elements.append((group, finite_elements, reference_elements, links))

		return list(node_map.values()), grouped_elements

	@staticmethod
	def _get_group_color(group_index: int) -> str:
		palette = (
			"tab:blue",
			"tab:orange",
			"tab:green",
			"tab:red",
			"tab:purple",
			"tab:brown",
			"tab:pink",
			"tab:gray",
			"tab:olive",
			"tab:cyan",
		)
		return palette[group_index % len(palette)]

	@staticmethod
	def _to_meter_value(value: Any) -> float:
		if hasattr(value, "to") and hasattr(value, "magnitude"):
			return float(value.to("meter").magnitude)
		return float(value)

	@staticmethod
	def _set_equal_3d_axes(ax: Any, nodes: list[Node]) -> None:
		"""Set balanced axis limits to avoid distorted 3D model proportions."""
		if not nodes:
			return

		x = [GeometryVisualizer._to_meter_value(node.X) for node in nodes]
		y = [GeometryVisualizer._to_meter_value(node.Y) for node in nodes]
		z = [GeometryVisualizer._to_meter_value(node.Z) for node in nodes]

		x_mid = (max(x) + min(x)) * 0.5
		y_mid = (max(y) + min(y)) * 0.5
		z_mid = (max(z) + min(z)) * 0.5
		span = max(max(x) - min(x), max(y) - min(y), max(z) - min(z), 1.0)
		radius = 0.5 * span

		ax.set_xlim(x_mid - radius, x_mid + radius)
		ax.set_ylim(y_mid - radius, y_mid + radius)
		ax.set_zlim(z_mid - radius, z_mid + radius)

	@staticmethod
	def _build_output_path(flat: bool, file_name: str | None, file_format: str) -> Path:
		if file_name is None:
			default_stem = "geometry_xy" if flat else "geometry_3d"
			normalized_format = file_format.lstrip(".")
			file_name = f"{default_stem}.{normalized_format}"

		return Path.cwd() / file_name



