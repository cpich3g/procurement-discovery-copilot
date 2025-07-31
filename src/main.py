"""
Main application interface for the Procurement Discovery Tool.

This module provides the primary interface for running procurement discovery workflows.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .workflow.procurement_workflow import create_procurement_workflow
from .config.settings import config
from .utils.logging import setup_logging, get_logger
from .utils.output_formatter import report_formatter

logger = get_logger(__name__)


class ProcurementDiscoveryApp:
    """Main application class for procurement discovery."""
    
    def __init__(self):
        """Initialize the procurement discovery application."""
        self.workflow = create_procurement_workflow()
        logger.info("Procurement Discovery Tool initialized")
    
    def discover(
        self, 
        service_name: str, 
        country: str, 
        additional_details: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run procurement discovery for a service.
        
        Args:
            service_name: Name of the service/product to discover
            country: Target country for procurement
            additional_details: Optional additional details about requirements
            output_file: Optional file path to save results
            
        Returns:
            Dictionary containing discovery results
        """
        logger.info(f"Starting procurement discovery: {service_name} in {country}")
        
        # Run the workflow
        results = self.workflow.run(
            service_name=service_name,
            country=country,
            additional_details=additional_details
        )
        
        # Save results to file if specified
        if output_file:
            self._save_results(results, output_file)
        
        return results
    
    async def adiscover(
        self, 
        service_name: str, 
        country: str, 
        additional_details: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async version of procurement discovery.
        
        Args:
            service_name: Name of the service/product to discover
            country: Target country for procurement
            additional_details: Optional additional details about requirements
            output_file: Optional file path to save results
            
        Returns:
            Dictionary containing discovery results
        """
        logger.info(f"Starting async procurement discovery: {service_name} in {country}")
        
        # Run the workflow asynchronously
        results = await self.workflow.arun(
            service_name=service_name,
            country=country,
            additional_details=additional_details
        )
        
        # Save results to file if specified
        if output_file:
            self._save_results(results, output_file)
        
        return results
    
    def _save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """Save results to a file in multiple formats based on file extension."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_extension = output_path.suffix.lower()
            
            if file_extension == '.html':
                # Save as HTML
                html_content = report_formatter.to_html(results)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"HTML report saved to {output_file}")
                
            elif file_extension in ['.md', '.markdown']:
                # Save as Markdown
                markdown_content = report_formatter.to_markdown(results)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Markdown report saved to {output_file}")
                
            else:
                # Default to JSON for .json or unknown extensions
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"JSON results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {str(e)}")
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print a summary of the results to console."""
        print("\n" + "="*80)
        print("PROCUREMENT DISCOVERY SUMMARY")
        print("="*80)
        
        if results.get("success"):
            print("✅ Discovery completed successfully!")
            
            summary = results.get("summary", {})
            metadata = results.get("metadata", {})
            
            print(f"\nService: {metadata.get('service_name', 'N/A')}")
            print(f"Country: {metadata.get('country', 'N/A')}")
            print(f"Session ID: {results.get('session_id', 'N/A')}")
            print(f"Processing Time: {results.get('processing_time', 'N/A')}")
            
            # Progress information
            progress = summary.get("progress", {})
            print(f"\nProgress: {progress.get('completed_steps', 0)}/{progress.get('total_steps', 4)} steps ({progress.get('percentage', 0):.1f}%)")
            
            # Report summary
            final_report = results.get("final_report", {})
            if final_report:
                print(f"\n📊 EXECUTIVE SUMMARY:")
                exec_summary = final_report.get("executive_summary", "")
                if exec_summary:
                    # Print first 300 characters of executive summary
                    print(exec_summary[:300] + ("..." if len(exec_summary) > 300 else ""))
                
                # Vendor count
                vendor_rankings = final_report.get("vendor_rankings", [])
                print(f"\n🏢 Vendors Found: {len(vendor_rankings)}")
                if vendor_rankings:
                    print("Top 3 Vendors:")
                    for i, vendor in enumerate(vendor_rankings[:3], 1):
                        print(f"  {i}. {vendor.get('vendor_name', 'N/A')} (Score: {vendor.get('overall_score', 0)}/100)")
                
                # Partner count
                partner_recommendations = final_report.get("partner_recommendations", [])
                print(f"\n🤝 Partners Found: {len(partner_recommendations)}")
                
                # Price information
                price_benchmarking = final_report.get("price_benchmarking", {})
                if price_benchmarking:
                    price_range_low = price_benchmarking.get("price_range_low")
                    price_range_high = price_benchmarking.get("price_range_high")
                    currency = price_benchmarking.get("currency", "USD")
                    if price_range_low and price_range_high:
                        print(f"\n💰 Price Range: {currency} {price_range_low:,.0f} - {currency} {price_range_high:,.0f}")
            
        else:
            print("❌ Discovery failed!")
            errors = results.get("errors", [])
            if errors:
                print("\nErrors:")
                for error in errors:
                    print(f"  • {error}")
        
        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            print(f"\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        print("\n" + "="*80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Procurement Discovery Tool - AI-powered vendor and partner discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m procurement_discovery "Cloud Storage" "United States"
  python -m procurement_discovery "ERP Software" "Germany" --details "Manufacturing company with 500 employees"
  python -m procurement_discovery "Marketing Automation" "Canada" --output results.json
  python -m procurement_discovery "CRM Software" "UK" --output report.html
  python -m procurement_discovery "Video Conferencing" "Australia" --output summary.md
        """
    )
    
    parser.add_argument(
        "service_name",
        help="Name of the service or product to discover"
    )
    
    parser.add_argument(
        "country", 
        help="Target country for procurement"
    )
    
    parser.add_argument(
        "--details",
        help="Additional details about requirements",
        default=None
    )
    
    parser.add_argument(
        "--output",
        help="Output file path to save results. Format determined by extension (.json, .html, .md/.markdown)",
        default=None
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true", 
        help="Suppress summary output (useful when saving to file)"
    )
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        log_level = "DEBUG" if args.verbose else "INFO"
        setup_logging(log_level=log_level)
        
        # Create and run the application
        app = ProcurementDiscoveryApp()
        
        print(f"🔍 Starting procurement discovery for '{args.service_name}' in {args.country}...")
        
        results = app.discover(
            service_name=args.service_name,
            country=args.country,
            additional_details=args.details,
            output_file=args.output
        )
        
        # Print summary unless quiet mode
        if not args.quiet:
            app.print_summary(results)
        
        # Exit with appropriate code
        exit_code = 0 if results.get("success") else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n❌ Discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"\n❌ Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
