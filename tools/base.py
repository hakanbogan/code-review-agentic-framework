"""Abstract base class for all code analysis tools."""

from abc import ABC, abstractmethod
from pathlib import Path
from time import time
from typing import Any, Dict, List

from domain import ToolResult


class BaseTool(ABC):
    """Base class for all analysis tools."""

    def __init__(self, name: str, executable_path: str):
        self.name = name
        self.executable_path = executable_path

    @abstractmethod
    def run(self, target_path: Path, **kwargs: Any) -> ToolResult:
        """Run the tool on target path.

        Args:
            target_path: Path to analyze (file or directory)
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with findings and metadata
        """
        pass

    @abstractmethod
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse tool output into structured format.

        Args:
            output: Raw tool output

        Returns:
            Structured data dictionary
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if tool is available on system."""
        pass

    def _execute_with_timing(self, func: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Execute function and return result with timing."""
        start = time()
        result = func(*args, **kwargs)
        elapsed = time() - start
        return result, elapsed

    def validate_target(self, target_path: Path) -> None:
        """Validate target path exists and is accessible.

        Args:
            target_path: Path to validate

        Raises:
            FileNotFoundError: If path doesn't exist
            PermissionError: If path isn't readable
        """
        if not target_path.exists():
            raise FileNotFoundError(f"Target path does not exist: {target_path}")
        if not target_path.is_file() and not target_path.is_dir():
            raise ValueError(f"Target must be file or directory: {target_path}")


class ToolRegistry:
    """Registry for managing tool instances."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        if not tool.is_available():
            raise RuntimeError(f"Tool not available: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Get tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]

    def get_all(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def is_registered(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools
