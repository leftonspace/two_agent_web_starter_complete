"""
Spreadsheet Integration Engine for JARVIS.

Provides natural language queries on spreadsheet data,
auto-generation of charts and reports, and data analysis.
"""

import re
import json
import csv
import io
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ChartType(Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    COLUMN = "column"
    DOUGHNUT = "doughnut"


class AggregationType(Enum):
    """Data aggregation types."""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"


@dataclass
class SpreadsheetData:
    """Represents spreadsheet data."""
    headers: List[str]
    rows: List[List[Any]]
    sheet_name: str = "Sheet1"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def column_count(self) -> int:
        return len(self.headers)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def get_column(self, name: str) -> List[Any]:
        """Get all values in a column by name."""
        if name not in self.headers:
            raise ValueError(f"Column '{name}' not found")
        idx = self.headers.index(name)
        return [row[idx] if idx < len(row) else None for row in self.rows]

    def get_numeric_columns(self) -> List[str]:
        """Get names of columns that contain numeric data."""
        numeric_cols = []
        for i, header in enumerate(self.headers):
            values = [row[i] for row in self.rows if i < len(row) and row[i] is not None]
            if values and all(self._is_numeric(v) for v in values[:10]):  # Check first 10
                numeric_cols.append(header)
        return numeric_cols

    def get_date_columns(self) -> List[str]:
        """Get names of columns that contain date data."""
        date_cols = []
        for i, header in enumerate(self.headers):
            values = [row[i] for row in self.rows if i < len(row) and row[i] is not None]
            if values and all(self._is_date(v) for v in values[:10]):
                date_cols.append(header)
        return date_cols

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        """Check if value is numeric."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(',', '').replace('$', '').replace('%', ''))
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def _is_date(value: Any) -> bool:
        """Check if value looks like a date."""
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{2}-\d{2}-\d{4}',
            ]
            return any(re.match(p, value) for p in date_patterns)
        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "headers": self.headers,
            "rows": self.rows,
            "sheet_name": self.sheet_name,
            "row_count": self.row_count,
            "column_count": self.column_count
        }


@dataclass
class QueryResult:
    """Result of a spreadsheet query."""
    success: bool
    data: Any = None
    visualization: Optional[Dict] = None
    summary: str = ""
    sql_equivalent: str = ""
    error: str = ""

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "visualization": self.visualization,
            "summary": self.summary,
            "sql_equivalent": self.sql_equivalent,
            "error": self.error
        }


class SpreadsheetEngine:
    """Engine for natural language spreadsheet queries."""

    def __init__(self):
        self.current_data: Optional[SpreadsheetData] = None

    def load_csv(self, content: str, sheet_name: str = "Sheet1") -> SpreadsheetData:
        """Load data from CSV content."""
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        if not rows:
            raise ValueError("Empty CSV data")

        headers = rows[0]
        data_rows = []

        for row in rows[1:]:
            # Convert numeric strings to numbers
            converted_row = []
            for val in row:
                converted_row.append(self._convert_value(val))
            data_rows.append(converted_row)

        self.current_data = SpreadsheetData(
            headers=headers,
            rows=data_rows,
            sheet_name=sheet_name
        )
        return self.current_data

    def load_json(self, content: str, sheet_name: str = "Sheet1") -> SpreadsheetData:
        """Load data from JSON content (array of objects)."""
        data = json.loads(content)

        if not isinstance(data, list) or not data:
            raise ValueError("JSON must be a non-empty array of objects")

        # Extract headers from first object
        headers = list(data[0].keys())

        # Convert to rows
        rows = []
        for item in data:
            row = [self._convert_value(item.get(h)) for h in headers]
            rows.append(row)

        self.current_data = SpreadsheetData(
            headers=headers,
            rows=rows,
            sheet_name=sheet_name
        )
        return self.current_data

    def _convert_value(self, val: Any) -> Any:
        """Convert string values to appropriate types."""
        if val is None or val == '':
            return None
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            # Try to convert to number
            cleaned = val.replace(',', '').replace('$', '').replace('%', '').strip()
            try:
                if '.' in cleaned:
                    return float(cleaned)
                return int(cleaned)
            except ValueError:
                pass
        return val

    def query(self, natural_language: str, data: Optional[SpreadsheetData] = None) -> QueryResult:
        """
        Execute a natural language query on spreadsheet data.

        This method parses natural language queries and translates them
        to data operations. For complex queries, it delegates to LLM.
        """
        data = data or self.current_data
        if not data:
            return QueryResult(success=False, error="No data loaded")

        query_lower = natural_language.lower()

        try:
            # Handle common query patterns
            if any(kw in query_lower for kw in ['sum', 'total', 'add up']):
                return self._handle_aggregation(query_lower, data, AggregationType.SUM)

            elif any(kw in query_lower for kw in ['average', 'avg', 'mean']):
                return self._handle_aggregation(query_lower, data, AggregationType.AVERAGE)

            elif any(kw in query_lower for kw in ['count', 'how many']):
                return self._handle_count(query_lower, data)

            elif any(kw in query_lower for kw in ['max', 'maximum', 'highest', 'largest']):
                return self._handle_aggregation(query_lower, data, AggregationType.MAX)

            elif any(kw in query_lower for kw in ['min', 'minimum', 'lowest', 'smallest']):
                return self._handle_aggregation(query_lower, data, AggregationType.MIN)

            elif any(kw in query_lower for kw in ['chart', 'graph', 'visualize', 'plot']):
                return self._handle_visualization(query_lower, data)

            elif any(kw in query_lower for kw in ['filter', 'where', 'only', 'show me']):
                return self._handle_filter(query_lower, data)

            elif any(kw in query_lower for kw in ['sort', 'order', 'rank']):
                return self._handle_sort(query_lower, data)

            elif any(kw in query_lower for kw in ['group by', 'breakdown', 'by category']):
                return self._handle_groupby(query_lower, data)

            elif any(kw in query_lower for kw in ['describe', 'summary', 'overview', 'statistics']):
                return self._handle_describe(data)

            else:
                # Return data summary for unrecognized queries
                return self._handle_describe(data)

        except Exception as e:
            return QueryResult(success=False, error=str(e))

    def _find_column(self, query: str, data: SpreadsheetData) -> Optional[str]:
        """Find the most likely column being referenced in the query."""
        query_lower = query.lower()

        # Direct match
        for header in data.headers:
            if header.lower() in query_lower:
                return header

        # Fuzzy match - check if any word in header appears in query
        for header in data.headers:
            words = header.lower().replace('_', ' ').split()
            if any(word in query_lower for word in words if len(word) > 2):
                return header

        # Return first numeric column as fallback
        numeric_cols = data.get_numeric_columns()
        return numeric_cols[0] if numeric_cols else None

    def _handle_aggregation(self, query: str, data: SpreadsheetData,
                           agg_type: AggregationType) -> QueryResult:
        """Handle sum, average, min, max queries."""
        column = self._find_column(query, data)
        if not column:
            return QueryResult(
                success=False,
                error="Could not identify which column to aggregate"
            )

        values = [v for v in data.get_column(column) if isinstance(v, (int, float))]

        if not values:
            return QueryResult(
                success=False,
                error=f"No numeric values found in column '{column}'"
            )

        if agg_type == AggregationType.SUM:
            result = sum(values)
            summary = f"The sum of {column} is {result:,.2f}"
            sql = f"SELECT SUM({column}) FROM {data.sheet_name}"
        elif agg_type == AggregationType.AVERAGE:
            result = sum(values) / len(values)
            summary = f"The average of {column} is {result:,.2f}"
            sql = f"SELECT AVG({column}) FROM {data.sheet_name}"
        elif agg_type == AggregationType.MAX:
            result = max(values)
            summary = f"The maximum value in {column} is {result:,.2f}"
            sql = f"SELECT MAX({column}) FROM {data.sheet_name}"
        elif agg_type == AggregationType.MIN:
            result = min(values)
            summary = f"The minimum value in {column} is {result:,.2f}"
            sql = f"SELECT MIN({column}) FROM {data.sheet_name}"
        else:
            result = sum(values)
            summary = f"Result: {result:,.2f}"
            sql = ""

        return QueryResult(
            success=True,
            data={"column": column, "result": result, "count": len(values)},
            summary=summary,
            sql_equivalent=sql
        )

    def _handle_count(self, query: str, data: SpreadsheetData) -> QueryResult:
        """Handle count queries."""
        # Check if counting specific column or rows
        column = self._find_column(query, data)

        if column:
            values = [v for v in data.get_column(column) if v is not None]
            count = len(values)
            summary = f"There are {count} values in {column}"
            sql = f"SELECT COUNT({column}) FROM {data.sheet_name}"
        else:
            count = data.row_count
            summary = f"There are {count} rows in the data"
            sql = f"SELECT COUNT(*) FROM {data.sheet_name}"

        return QueryResult(
            success=True,
            data={"count": count},
            summary=summary,
            sql_equivalent=sql
        )

    def _handle_visualization(self, query: str, data: SpreadsheetData) -> QueryResult:
        """Generate chart configuration."""
        query_lower = query.lower()

        # Determine chart type
        if 'pie' in query_lower:
            chart_type = ChartType.PIE
        elif 'line' in query_lower:
            chart_type = ChartType.LINE
        elif 'scatter' in query_lower:
            chart_type = ChartType.SCATTER
        elif 'area' in query_lower:
            chart_type = ChartType.AREA
        else:
            chart_type = ChartType.BAR

        # Find columns to visualize
        numeric_cols = data.get_numeric_columns()
        all_cols = data.headers

        # Try to identify x and y columns
        x_col = None
        y_col = None

        for col in all_cols:
            if col.lower() not in [c.lower() for c in numeric_cols]:
                x_col = col
                break

        if numeric_cols:
            y_col = self._find_column(query, data) or numeric_cols[0]

        if not x_col:
            x_col = data.headers[0]
        if not y_col and numeric_cols:
            y_col = numeric_cols[0]

        # Build chart data
        labels = data.get_column(x_col) if x_col else list(range(data.row_count))
        values = data.get_column(y_col) if y_col else []

        chart_config = {
            "type": chart_type.value,
            "data": {
                "labels": [str(l) for l in labels[:50]],  # Limit to 50 points
                "datasets": [{
                    "label": y_col or "Values",
                    "data": [v if isinstance(v, (int, float)) else 0 for v in values[:50]]
                }]
            },
            "options": {
                "title": f"{y_col} by {x_col}" if x_col and y_col else "Data Visualization"
            }
        }

        return QueryResult(
            success=True,
            visualization=chart_config,
            summary=f"Generated {chart_type.value} chart showing {y_col} by {x_col}"
        )

    def _handle_filter(self, query: str, data: SpreadsheetData) -> QueryResult:
        """Handle filter/where queries."""
        # Simple pattern matching for common filters
        patterns = [
            (r'where (\w+)\s*[=>]+\s*(\d+)', 'gte'),
            (r'where (\w+)\s*[<]+\s*(\d+)', 'lt'),
            (r'where (\w+)\s*=\s*["\']?(\w+)["\']?', 'eq'),
            (r'(\w+)\s*greater than\s*(\d+)', 'gt'),
            (r'(\w+)\s*less than\s*(\d+)', 'lt'),
        ]

        for pattern, op in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                col_hint, value = match.groups()
                column = self._find_column(col_hint, data)
                if column:
                    return self._apply_filter(data, column, op, value)

        return QueryResult(
            success=False,
            error="Could not parse filter condition. Try: 'where [column] > [value]'"
        )

    def _apply_filter(self, data: SpreadsheetData, column: str,
                     op: str, value: Any) -> QueryResult:
        """Apply filter to data."""
        col_idx = data.headers.index(column)

        try:
            value = float(value)
        except ValueError:
            pass

        filtered_rows = []
        for row in data.rows:
            cell_value = row[col_idx] if col_idx < len(row) else None

            if cell_value is None:
                continue

            if op == 'eq' and str(cell_value).lower() == str(value).lower():
                filtered_rows.append(row)
            elif op == 'gt' and isinstance(cell_value, (int, float)) and cell_value > value:
                filtered_rows.append(row)
            elif op == 'gte' and isinstance(cell_value, (int, float)) and cell_value >= value:
                filtered_rows.append(row)
            elif op == 'lt' and isinstance(cell_value, (int, float)) and cell_value < value:
                filtered_rows.append(row)

        return QueryResult(
            success=True,
            data={
                "headers": data.headers,
                "rows": filtered_rows[:100],  # Limit results
                "total_matches": len(filtered_rows)
            },
            summary=f"Found {len(filtered_rows)} rows where {column} {op} {value}",
            sql_equivalent=f"SELECT * FROM {data.sheet_name} WHERE {column} {self._op_to_sql(op)} {value}"
        )

    def _op_to_sql(self, op: str) -> str:
        """Convert operation to SQL operator."""
        return {'eq': '=', 'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<='}.get(op, '=')

    def _handle_sort(self, query: str, data: SpreadsheetData) -> QueryResult:
        """Handle sort queries."""
        column = self._find_column(query, data)
        if not column:
            column = data.headers[0]

        descending = any(kw in query.lower() for kw in ['desc', 'descending', 'highest', 'largest'])

        col_idx = data.headers.index(column)
        sorted_rows = sorted(
            data.rows,
            key=lambda r: (r[col_idx] if col_idx < len(r) and r[col_idx] is not None else 0),
            reverse=descending
        )

        order = "DESC" if descending else "ASC"

        return QueryResult(
            success=True,
            data={
                "headers": data.headers,
                "rows": sorted_rows[:100]
            },
            summary=f"Data sorted by {column} ({order})",
            sql_equivalent=f"SELECT * FROM {data.sheet_name} ORDER BY {column} {order}"
        )

    def _handle_groupby(self, query: str, data: SpreadsheetData) -> QueryResult:
        """Handle group by queries."""
        # Find grouping column (usually non-numeric)
        group_col = None
        for col in data.headers:
            if col not in data.get_numeric_columns():
                if col.lower() in query.lower():
                    group_col = col
                    break

        if not group_col:
            # Use first non-numeric column
            for col in data.headers:
                if col not in data.get_numeric_columns():
                    group_col = col
                    break

        if not group_col:
            return QueryResult(success=False, error="No categorical column found for grouping")

        # Find numeric column to aggregate
        agg_col = self._find_column(query, data)
        if agg_col == group_col:
            numeric_cols = data.get_numeric_columns()
            agg_col = numeric_cols[0] if numeric_cols else None

        if not agg_col:
            return QueryResult(success=False, error="No numeric column found for aggregation")

        # Perform grouping
        groups: Dict[str, List[float]] = {}
        group_idx = data.headers.index(group_col)
        agg_idx = data.headers.index(agg_col)

        for row in data.rows:
            key = str(row[group_idx]) if group_idx < len(row) else "Unknown"
            value = row[agg_idx] if agg_idx < len(row) else None

            if isinstance(value, (int, float)):
                if key not in groups:
                    groups[key] = []
                groups[key].append(value)

        # Calculate sums
        result = {k: sum(v) for k, v in groups.items()}

        return QueryResult(
            success=True,
            data={"groups": result, "group_column": group_col, "value_column": agg_col},
            visualization={
                "type": "bar",
                "data": {
                    "labels": list(result.keys()),
                    "datasets": [{
                        "label": f"Sum of {agg_col}",
                        "data": list(result.values())
                    }]
                }
            },
            summary=f"Grouped {agg_col} by {group_col}",
            sql_equivalent=f"SELECT {group_col}, SUM({agg_col}) FROM {data.sheet_name} GROUP BY {group_col}"
        )

    def _handle_describe(self, data: SpreadsheetData) -> QueryResult:
        """Generate descriptive statistics."""
        stats = {
            "row_count": data.row_count,
            "column_count": data.column_count,
            "columns": {}
        }

        for col in data.headers:
            values = data.get_column(col)
            non_null = [v for v in values if v is not None]

            col_stats = {
                "non_null_count": len(non_null),
                "null_count": len(values) - len(non_null)
            }

            # Add numeric stats if applicable
            numeric_values = [v for v in non_null if isinstance(v, (int, float))]
            if numeric_values:
                col_stats.update({
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "sum": sum(numeric_values),
                    "average": sum(numeric_values) / len(numeric_values)
                })

            stats["columns"][col] = col_stats

        summary_lines = [
            f"Dataset: {data.sheet_name}",
            f"Rows: {data.row_count}, Columns: {data.column_count}",
            "",
            "Column Statistics:"
        ]

        for col, col_stats in stats["columns"].items():
            if "average" in col_stats:
                summary_lines.append(
                    f"  {col}: avg={col_stats['average']:,.2f}, "
                    f"min={col_stats['min']:,.2f}, max={col_stats['max']:,.2f}"
                )
            else:
                summary_lines.append(f"  {col}: {col_stats['non_null_count']} values")

        return QueryResult(
            success=True,
            data=stats,
            summary="\n".join(summary_lines)
        )

    def generate_formula(self, description: str, data: Optional[SpreadsheetData] = None) -> Dict:
        """Generate Excel/Sheets formula from description."""
        data = data or self.current_data
        description_lower = description.lower()

        # Common formula patterns
        formulas = []

        if 'sum' in description_lower:
            col = self._find_column(description, data) if data else 'A'
            col_letter = chr(65 + data.headers.index(col)) if data and col in data.headers else 'A'
            formulas.append({
                "excel": f"=SUM({col_letter}:{col_letter})",
                "sheets": f"=SUM({col_letter}:{col_letter})",
                "description": f"Sum all values in column {col}"
            })

        if 'average' in description_lower or 'avg' in description_lower:
            col = self._find_column(description, data) if data else 'A'
            col_letter = chr(65 + data.headers.index(col)) if data and col in data.headers else 'A'
            formulas.append({
                "excel": f"=AVERAGE({col_letter}:{col_letter})",
                "sheets": f"=AVERAGE({col_letter}:{col_letter})",
                "description": f"Average of column {col}"
            })

        if 'count' in description_lower:
            col = self._find_column(description, data) if data else 'A'
            col_letter = chr(65 + data.headers.index(col)) if data and col in data.headers else 'A'
            formulas.append({
                "excel": f"=COUNTA({col_letter}:{col_letter})",
                "sheets": f"=COUNTA({col_letter}:{col_letter})",
                "description": f"Count non-empty cells in column {col}"
            })

        if 'vlookup' in description_lower or 'lookup' in description_lower:
            formulas.append({
                "excel": "=VLOOKUP(lookup_value, table_array, col_index, FALSE)",
                "sheets": "=VLOOKUP(search_key, range, index, FALSE)",
                "description": "Lookup a value in a table"
            })

        if 'if' in description_lower:
            formulas.append({
                "excel": "=IF(condition, value_if_true, value_if_false)",
                "sheets": "=IF(condition, value_if_true, value_if_false)",
                "description": "Conditional formula"
            })

        if not formulas:
            formulas.append({
                "excel": "Formula not recognized",
                "sheets": "Formula not recognized",
                "description": "Try: sum, average, count, vlookup, if"
            })

        return {"formulas": formulas}


# Singleton instance
_spreadsheet_engine = None

def get_spreadsheet_engine() -> SpreadsheetEngine:
    """Get or create the spreadsheet engine instance."""
    global _spreadsheet_engine
    if _spreadsheet_engine is None:
        _spreadsheet_engine = SpreadsheetEngine()
    return _spreadsheet_engine
