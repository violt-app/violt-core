"""
Violt Core - Template System

This module implements template support for automations using Jinja2.
"""

from typing import Dict, Any, Optional
import logging
from jinja2 import Environment, Template, meta
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages template rendering and validation."""

    def __init__(self):
        self.env = Environment(
            trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True
        )
        self._add_filters()
        self._add_functions()

    def _add_filters(self):
        """Add custom filters to the Jinja2 environment."""
        self.env.filters.update(
            {
                "timestamp_custom": lambda dt, fmt: dt.strftime(fmt) if dt else "",
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else 0,
                "round": lambda x, digits=0: round(x, digits),
                "timestamp": lambda dt: dt.timestamp() if dt else 0,
                "json_dumps": lambda x: json.dumps(x),
                "json_loads": lambda x: json.loads(x),
            }
        )

    def _add_functions(self):
        """Add custom functions to the Jinja2 environment."""
        self.env.globals.update(
            {
                "now": datetime.now,
                "utcnow": lambda: datetime.now(datetime.timezone.utc),
                "states": lambda entity_id: self._get_state(entity_id),
                "is_state": lambda entity_id, state: self._is_state(entity_id, state),
                "state_attr": lambda entity_id, attr: self._get_state_attr(
                    entity_id, attr
                ),
            }
        )

    def _get_state(self, entity_id: str) -> Optional[str]:
        """Get the state of an entity."""
        from ..core.state import state_manager

        state = state_manager.get_state(entity_id)
        return state.state if state else None

    def _is_state(self, entity_id: str, state: str) -> bool:
        """Check if an entity is in a specific state."""
        return self._get_state(entity_id) == state

    def _get_state_attr(self, entity_id: str, attr: str) -> Any:
        """Get an attribute of an entity's state."""
        from ..core.state import state_manager

        state = state_manager.get_state(entity_id)
        return state.attributes.get(attr) if state else None

    def render_template(
        self, template_str: str, variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render a template string with the given variables."""
        try:
            template = self.env.from_string(template_str)
            return template.render(**(variables or {}))
        except Exception as e:
            logger.error(f"Error rendering template: {e}", exc_info=True)
            raise

    def validate_template(self, template_str: str) -> bool:
        """Validate a template string."""
        try:
            self.env.parse(template_str)
            return True
        except Exception as e:
            logger.error(f"Invalid template: {e}", exc_info=True)
            return False

    def get_template_variables(self, template_str: str) -> set:
        """Get all variables used in a template."""
        try:
            ast = self.env.parse(template_str)
            return meta.find_undeclared_variables(ast)
        except Exception as e:
            logger.error(f"Error getting template variables: {e}", exc_info=True)
            return set()


# Global template manager instance
template_manager = TemplateManager()
