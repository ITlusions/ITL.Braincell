"""Cell auto-discovery.

Scans ``src/cells/*/cell.py`` for a module-level ``cell`` object that is an
instance of :class:`~src.cells.base.MemoryCell`.  Every matching module
is loaded and its cell registered automatically — no manual imports needed."""
import importlib
import logging
from pathlib import Path
from typing import List

from src.cells.base import MemoryCell

logger = logging.getLogger(__name__)

_CELLS_DIR = Path(__file__).parent


def discover_cells() -> List[MemoryCell]:
    """Return all valid cells found under src/cells/.

    Cells are discovered by scanning for ``src/cells/<name>/cell.py`` files
    that export a module-level attribute ``cell`` which is a
    :class:`MemoryCell` instance.
    """
    cells: List[MemoryCell] = []

    for child in sorted(_CELLS_DIR.iterdir()):
        # Skip non-directories and private/dunder folders
        if not child.is_dir() or child.name.startswith("_"):
            continue

        cell_module_file = child / "cell.py"
        if not cell_module_file.exists():
            continue

        module_name = f"src.cells.{child.name}.cell"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            logger.error("Failed to import cell module %s: %s", module_name, exc)
            continue

        cell_obj = getattr(module, "cell", None)
        if not isinstance(cell_obj, MemoryCell):
            logger.warning(
                "Cell module %s does not export a valid 'cell' instance — skipped.",
                module_name,
            )
            continue

        cells.append(cell_obj)
        logger.info("Discovered cell: %s (%s)", cell_obj.name, cell_obj.prefix)

    return cells
