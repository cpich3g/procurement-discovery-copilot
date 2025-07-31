"""
Output formatters for the Procurement Discovery Tool.

This module provides formatting capabilities for reports in various output formats.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class ReportFormatter:
    """Formatter for procurement discovery reports."""
    
    def __init__(self):
        """Initialize the report formatter."""
        pass
    
    def to_json(self, report_data: Dict[str, Any], indent: int = 2) -> str:
        """
        Format report data as JSON.
        
        Args:
            report_data: Report data dictionary
            indent: JSON indentation
            
        Returns:
            str: JSON formatted report
        """
        return json.dumps(report_data, indent=indent, default=str)
    
    def to_markdown(self, report_data: Dict[str, Any]) -> str:
        """
        Format report data as Markdown.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            str: Markdown formatted report
        """
        # Ensure report_data is a dictionary
        if not isinstance(report_data, dict):
            report_data = {}
        
        md_content = []
        
        # Header
        service_name = self._get_nested_value(report_data, ["metadata", "service_name"], "Unknown Service")
        country = self._get_nested_value(report_data, ["metadata", "country"], "Unknown")
        
        md_content.append(f"# Procurement Discovery Report: {service_name}")
        md_content.append(f"**Target Country:** {country}")
        
        # Get timestamp
        timestamp = self._get_nested_value(report_data, ["metadata", "completed_at"], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        md_content.append(f"**Generated:** {timestamp}")
        md_content.append("")
        
        # Executive Summary
        final_report = report_data.get("final_report") if report_data else None
        if final_report and isinstance(final_report, dict) and "executive_summary" in final_report:
            md_content.append("## 📋 Executive Summary")
            md_content.append(final_report["executive_summary"])
            md_content.append("")
        elif not final_report:
            md_content.append("## ⚠️ Report Generation Failed")
            md_content.append("The procurement discovery process encountered issues and could not generate a complete report.")
            
            # Add error information if available
            errors = report_data.get("errors", []) if report_data else []
            if errors:
                md_content.append("")
                md_content.append("**Errors encountered:**")
                for error in errors:
                    md_content.append(f"- {error}")
            
            md_content.append("")
            return "\n".join(md_content)
        
        # Service Analysis
        service_analysis = final_report.get("service_analysis", {})
        if service_analysis:
            md_content.append("## 🔍 Service Analysis")
            
            if "service_overview" in service_analysis:
                md_content.append("### Overview")
                md_content.append(service_analysis["service_overview"])
                md_content.append("")
            
            if "key_features" in service_analysis and service_analysis["key_features"]:
                md_content.append("### Key Features")
                for feature in service_analysis["key_features"]:
                    md_content.append(f"- {feature}")
                md_content.append("")
            
            if "technical_specifications" in service_analysis and service_analysis["technical_specifications"]:
                md_content.append("### Technical Requirements")
                for spec in service_analysis["technical_specifications"]:
                    md_content.append(f"- {spec}")
                md_content.append("")
        
        # Vendor Rankings
        vendor_rankings = final_report.get("vendor_rankings", [])
        if vendor_rankings:
            md_content.append("## 🏆 Vendor Rankings")
            
            for i, vendor in enumerate(vendor_rankings, 1):
                score = vendor.get("overall_score", 0)
                vendor_name = vendor.get('vendor_name', 'Unknown Vendor')
                md_content.append(f"### {i}. {vendor_name} ({score}/100)")
                
                description = vendor.get("description", "")
                if description:
                    md_content.append(f"**Description:** {description}")
                    md_content.append("")
                
                if "strengths" in vendor and vendor["strengths"]:
                    md_content.append("**Strengths:**")
                    for strength in vendor["strengths"]:
                        md_content.append(f"- {strength}")
                    md_content.append("")
                
                if "weaknesses" in vendor and vendor["weaknesses"]:
                    md_content.append("**Areas for Consideration:**")
                    for weakness in vendor["weaknesses"]:
                        md_content.append(f"- {weakness}")
                    md_content.append("")
        
        # Partner Recommendations
        partner_recommendations = final_report.get("partner_recommendations", [])
        if partner_recommendations:
            md_content.append("## 🤝 Partner Recommendations")
            
            for i, partner in enumerate(partner_recommendations, 1):
                partner_name = partner.get("partner_name", "Unknown Partner")
                md_content.append(f"### {i}. {partner_name}")
                
                services = partner.get("services", [])
                if services:
                    md_content.append(f"**Services:** {', '.join(services)}")
                
                expertise = partner.get("expertise", "")
                if expertise:
                    md_content.append(f"**Expertise:** {expertise}")
                
                location = partner.get("location", "")
                if location:
                    md_content.append(f"**Location:** {location}")
                
                md_content.append("")
        
        # Price Benchmarking
        price_benchmarking = final_report.get("price_benchmarking", {})
        if price_benchmarking:
            md_content.append("## 💰 Price Benchmarking")
            
            price_low = price_benchmarking.get("price_range_low")
            price_high = price_benchmarking.get("price_range_high")
            currency = price_benchmarking.get("currency", "USD")
            
            if price_low and price_high:
                md_content.append(f"**Estimated Price Range:** {currency} {price_low:,.0f} - {currency} {price_high:,.0f}")
                md_content.append("")
            
            cost_breakdown = price_benchmarking.get("cost_breakdown", {})
            if cost_breakdown:
                md_content.append("**Cost Breakdown:**")
                if isinstance(cost_breakdown, dict):
                    for category, cost in cost_breakdown.items():
                        md_content.append(f"- **{category.replace('_', ' ').title()}:** {cost}")
                elif isinstance(cost_breakdown, list):
                    for item in cost_breakdown:
                        md_content.append(f"- {item}")
                md_content.append("")
            
            if "market_average" in price_benchmarking:
                currency = price_benchmarking.get("currency", "USD")
                avg = price_benchmarking["market_average"]
                md_content.append(f"**Market Average:** {currency} {avg:,.2f}")
                md_content.append("")
            
            if "factors_affecting_price" in price_benchmarking and price_benchmarking["factors_affecting_price"]:
                md_content.append("**Factors Affecting Price:**")
                for factor in price_benchmarking["factors_affecting_price"]:
                    md_content.append(f"- {factor}")
                md_content.append("")
        
        # Implementation Roadmap
        implementation_roadmap = final_report.get("implementation_roadmap", {})
        if implementation_roadmap:
            md_content.append("## 🛣️ Implementation Roadmap")
            if isinstance(implementation_roadmap, dict):
                for phase_name, phase_data in implementation_roadmap.items():
                    if isinstance(phase_data, dict):
                        md_content.append(f"### {phase_name.replace('_', ' ').title()}")
                        duration = phase_data.get("duration", "N/A")
                        md_content.append(f"**Duration:** {duration}")
                        
                        activities = phase_data.get("activities", [])
                        if activities:
                            md_content.append("**Activities:**")
                            for activity in activities:
                                md_content.append(f"- {activity}")
                        md_content.append("")
            elif isinstance(implementation_roadmap, list):
                for i, step in enumerate(implementation_roadmap, 1):
                    md_content.append(f"{i}. {step}")
                md_content.append("")
            
        # Risk Assessment
        risk_assessment = final_report.get("risk_assessment", [])
        if risk_assessment:
            md_content.append("## ⚠️ Risk Assessment")
            
            if isinstance(risk_assessment, dict):
                # Handle dictionary format
                risks = risk_assessment.get("risks", [])
                if risks:
                    for risk in risks:
                        if isinstance(risk, dict):
                            risk_name = risk.get("risk", "Unknown Risk")
                            severity = risk.get("severity", "Unknown")
                            md_content.append(f"- **{risk_name}** (Severity: {severity})")
                        else:
                            md_content.append(f"- {risk}")
            elif isinstance(risk_assessment, list):
                # Handle list format (direct list of risks)
                for risk in risk_assessment:
                    md_content.append(f"- {risk}")
            md_content.append("")
        
        # Next Steps
        next_steps = final_report.get("next_steps", [])
        if next_steps:
            md_content.append("## ➡️ Next Steps")
            for i, step in enumerate(next_steps, 1):
                md_content.append(f"{i}. {step}")
            md_content.append("")
        
        # Key Findings
        key_findings = final_report.get("key_findings", [])
        if key_findings:
            md_content.append("## 🔍 Key Findings")
            for finding in key_findings:
                md_content.append(f"- {finding}")
            md_content.append("")
        
        # Processing Information
        if report_data.get("success"):
            md_content.append("## 📋 Processing Information")
            processing_time = report_data.get("processing_time", "Unknown")
            session_id = report_data.get("session_id", "Unknown")
            md_content.append(f"**Processing Time:** {processing_time}")
            md_content.append(f"**Session ID:** {session_id}")
            
            # Warnings
            warnings = report_data.get("warnings", [])
            if warnings:
                md_content.append("")
                md_content.append("**Warnings:**")
                for warning in warnings:
                    md_content.append(f"- {warning}")
                md_content.append("")
        
        # Metadata
        if "generation_metadata" in report_data:
            metadata = report_data["generation_metadata"]
            md_content.append("## 📄 Report Information")
            md_content.append(f"- **Session ID:** {metadata.get('session_id', 'N/A')}")
            md_content.append(f"- **Processing Time:** {metadata.get('processing_time', 'N/A')}")
            md_content.append(f"- **Data Sources:** {', '.join(metadata.get('data_sources', []))}")
            md_content.append(f"- **Report Version:** {metadata.get('report_version', 'N/A')}")
        
        return "\n".join(md_content)
    
    def to_html(self, report_data: Dict[str, Any]) -> str:
        """
        Format report data as HTML.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            str: HTML formatted report
        """
        # Ensure report_data is a dictionary
        if not isinstance(report_data, dict):
            report_data = {}
        
        # Convert to markdown first, then to HTML
        try:
            markdown_content = self.to_markdown(report_data)
        except Exception as e:
            # Fallback if markdown generation fails
            markdown_content = f"# Report Generation Error\n\nFailed to generate report: {str(e)}"
        
        # Simple markdown to HTML conversion
        html_content = []
        html_content.append("<!DOCTYPE html>")
        html_content.append("<html lang='en'>")
        html_content.append("<head>")
        html_content.append("    <meta charset='UTF-8'>")
        html_content.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        
        service_name = self._get_nested_value(report_data, ["metadata", "service_name"], "Procurement Report")
        html_content.append(f"    <title>{service_name} - Procurement Discovery Report</title>")
        
        # Add CSS styling
        html_content.append("    <style>")
        html_content.append(self._get_html_styles())
        html_content.append("    </style>")
        html_content.append("</head>")
        html_content.append("<body>")
        html_content.append("    <div class='container'>")
        
        # Convert markdown to HTML (basic conversion)
        html_body = self._markdown_to_html(markdown_content)
        html_content.append(html_body)
        
        html_content.append("    </div>")
        html_content.append("</body>")
        html_content.append("</html>")
        
        return "\n".join(html_content)
    
    def _get_nested_value(self, data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
        """Get nested value from dictionary with fallback."""
        if not isinstance(data, dict):
            return default
            
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #2980b9;
            margin-top: 20px;
        }
        ul, ol {
            padding-left: 20px;
        }
        li {
            margin-bottom: 5px;
        }
        strong {
            color: #2c3e50;
        }
        .vendor-score {
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-top: 30px;
        }
        """
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        lines = markdown.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append("<br>")
                continue
            
            # Headers
            if line.startswith('# '):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h3>{line[4:]}</h3>")
            # List items
            elif line.startswith('- '):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                content = line[2:]
                # Handle bold text
                content = content.replace('**', '<strong>').replace('**', '</strong>')
                html_lines.append(f"<li>{content}</li>")
            # Numbered lists
            elif line and line[0].isdigit() and '. ' in line:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                content = line.split('. ', 1)[1] if '. ' in line else line
                html_lines.append(f"<p><strong>{line.split('.')[0]}.</strong> {content}</p>")
            # Regular paragraphs
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                # Handle bold text
                line = line.replace('**', '<strong>').replace('**', '</strong>')
                html_lines.append(f"<p>{line}</p>")
        
        if in_list:
            html_lines.append("</ul>")
        
        return "\n".join(html_lines)
    
    def save_report(self, report_data: Dict[str, Any], file_path: str, format_type: str = "auto") -> str:
        """
        Save report to file in specified format.
        
        Args:
            report_data: Report data dictionary
            file_path: Output file path
            format_type: Format type ('json', 'markdown', 'html', 'auto')
            
        Returns:
            str: Path to saved file
        """
        file_path = Path(file_path)
        
        # Auto-detect format from extension
        if format_type == "auto":
            extension = file_path.suffix.lower()
            if extension == ".json":
                format_type = "json"
            elif extension == ".md":
                format_type = "markdown"
            elif extension == ".html":
                format_type = "html"
            else:
                format_type = "json"
        
        # Generate content based on format
        if format_type == "json":
            content = self.to_json(report_data)
        elif format_type == "markdown":
            content = self.to_markdown(report_data)
        elif format_type == "html":
            content = self.to_html(report_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Save to file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        return str(file_path)


# Global formatter instance
report_formatter = ReportFormatter()
