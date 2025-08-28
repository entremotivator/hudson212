import json
import pandas as pd
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


def export_to_json(search_data, search_id=None):
    """
    Export search data to JSON format.
    
    Args:
        search_data: Search data dictionary
        search_id: Optional search ID for filename
    
    Returns:
        tuple: (json_string, filename)
    """
    try:
        json_string = json.dumps(search_data, indent=2, default=str)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"property_search_{search_id or 'export'}_{timestamp}.json"
        return json_string, filename
    except Exception as e:
        raise Exception(f"JSON export failed: {str(e)}")


def export_to_csv(search_results, search_id=None):
    """
    Export search results to CSV format.
    
    Args:
        search_results: List of property results
        search_id: Optional search ID for filename
    
    Returns:
        tuple: (csv_string, filename)
    """
    try:
        if not search_results:
            raise Exception("No search results to export")
        
        # Extract property data
        df_data = []
        for prop in search_results:
            row = {
                "Address": prop.get("formattedAddress", "N/A"),
                "City": prop.get("city", "N/A"),
                "State": prop.get("state", "N/A"),
                "ZIP Code": prop.get("zipCode", "N/A"),
                "Property Type": prop.get("propertyType", "N/A"),
                "Bedrooms": prop.get("bedrooms", "N/A"),
                "Bathrooms": prop.get("bathrooms", "N/A"),
                "Square Footage": prop.get("squareFootage", "N/A"),
                "Lot Size": prop.get("lotSize", "N/A"),
                "Year Built": prop.get("yearBuilt", "N/A"),
                "Last Sale Price": prop.get("lastSalePrice", "N/A"),
                "Last Sale Date": prop.get("lastSaleDate", "N/A"),
                "Owner Occupied": "Yes" if prop.get("ownerOccupied") else "No",
                "Assessor ID": prop.get("assessorID", "N/A"),
                "County": prop.get("county", "N/A"),
                "Zoning": prop.get("zoning", "N/A")
            }
            
            # Add owner information if available
            if "owner" in prop and prop["owner"]:
                owner = prop["owner"]
                names = owner.get("names", [])
                row["Owner Names"] = ", ".join(names) if names else "N/A"
                row["Owner Type"] = owner.get("type", "N/A")
            else:
                row["Owner Names"] = "N/A"
                row["Owner Type"] = "N/A"
            
            # Add features if available
            if "features" in prop and prop["features"]:
                features = prop["features"]
                row["Architecture Type"] = features.get("architectureType", "N/A")
                row["Exterior Type"] = features.get("exteriorType", "N/A")
                row["Heating"] = "Yes" if features.get("heating") else "No"
                row["Cooling"] = "Yes" if features.get("cooling") else "No"
                row["Garage"] = "Yes" if features.get("garage") else "No"
                row["Garage Spaces"] = features.get("garageSpaces", "N/A")
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        csv_string = df.to_csv(index=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"property_search_{search_id or 'export'}_{timestamp}.csv"
        
        return csv_string, filename
        
    except Exception as e:
        raise Exception(f"CSV export failed: {str(e)}")


def export_to_excel(search_results, search_metadata=None, search_id=None):
    """
    Export search results to Excel format with multiple sheets.
    
    Args:
        search_results: List of property results
        search_metadata: Optional metadata about the search
        search_id: Optional search ID for filename
    
    Returns:
        tuple: (excel_bytes, filename)
    """
    try:
        if not search_results:
            raise Exception("No search results to export")
        
        # Create Excel writer
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main properties sheet
            df_data = []
            for prop in search_results:
                row = {
                    "Address": prop.get("formattedAddress", "N/A"),
                    "City": prop.get("city", "N/A"),
                    "State": prop.get("state", "N/A"),
                    "ZIP Code": prop.get("zipCode", "N/A"),
                    "Property Type": prop.get("propertyType", "N/A"),
                    "Bedrooms": prop.get("bedrooms", "N/A"),
                    "Bathrooms": prop.get("bathrooms", "N/A"),
                    "Square Footage": prop.get("squareFootage", "N/A"),
                    "Lot Size": prop.get("lotSize", "N/A"),
                    "Year Built": prop.get("yearBuilt", "N/A"),
                    "Last Sale Price": prop.get("lastSalePrice", "N/A"),
                    "Last Sale Date": prop.get("lastSaleDate", "N/A"),
                    "Owner Occupied": "Yes" if prop.get("ownerOccupied") else "No",
                    "County": prop.get("county", "N/A"),
                    "Zoning": prop.get("zoning", "N/A")
                }
                df_data.append(row)
            
            df_main = pd.DataFrame(df_data)
            df_main.to_excel(writer, sheet_name='Properties', index=False)
            
            # Tax assessments sheet
            tax_data = []
            for i, prop in enumerate(search_results):
                if "taxAssessments" in prop and prop["taxAssessments"]:
                    for year, data in prop["taxAssessments"].items():
                        tax_data.append({
                            "Property Index": i + 1,
                            "Address": prop.get("formattedAddress", "N/A"),
                            "Year": year,
                            "Total Value": data.get("value", "N/A"),
                            "Land Value": data.get("land", "N/A"),
                            "Improvements": data.get("improvements", "N/A")
                        })
            
            if tax_data:
                df_tax = pd.DataFrame(tax_data)
                df_tax.to_excel(writer, sheet_name='Tax Assessments', index=False)
            
            # Property taxes sheet
            property_tax_data = []
            for i, prop in enumerate(search_results):
                if "propertyTaxes" in prop and prop["propertyTaxes"]:
                    for year, data in prop["propertyTaxes"].items():
                        property_tax_data.append({
                            "Property Index": i + 1,
                            "Address": prop.get("formattedAddress", "N/A"),
                            "Year": year,
                            "Total Tax": data.get("total", "N/A")
                        })
            
            if property_tax_data:
                df_prop_tax = pd.DataFrame(property_tax_data)
                df_prop_tax.to_excel(writer, sheet_name='Property Taxes', index=False)
            
            # Search metadata sheet
            if search_metadata:
                metadata_data = []
                for key, value in search_metadata.items():
                    metadata_data.append({"Field": key, "Value": str(value)})
                
                df_metadata = pd.DataFrame(metadata_data)
                df_metadata.to_excel(writer, sheet_name='Search Info', index=False)
        
        excel_bytes = output.getvalue()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"property_search_{search_id or 'export'}_{timestamp}.xlsx"
        
        return excel_bytes, filename
        
    except Exception as e:
        raise Exception(f"Excel export failed: {str(e)}")


def export_to_pdf_report(search_results, search_metadata=None, search_id=None):
    """
    Export search results to PDF report format.
    
    Args:
        search_results: List of property results
        search_metadata: Optional metadata about the search
        search_id: Optional search ID for filename
    
    Returns:
        tuple: (pdf_bytes, filename)
    """
    try:
        if not search_results:
            raise Exception("No search results to export")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12
        )
        
        # Build content
        content = []
        
        # Title
        title = Paragraph("Property Search Report", title_style)
        content.append(title)
        
        # Search metadata
        if search_metadata:
            content.append(Paragraph("Search Information", heading_style))
            
            metadata_data = []
            for key, value in search_metadata.items():
                if key != "results":  # Skip results data
                    metadata_data.append([str(key).replace("_", " ").title(), str(value)])
            
            if metadata_data:
                metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
                metadata_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                content.append(metadata_table)
                content.append(Spacer(1, 20))
        
        # Properties summary
        content.append(Paragraph(f"Properties Found: {len(search_results)}", heading_style))
        
        # Property details
        for i, prop in enumerate(search_results, 1):
            content.append(Paragraph(f"Property {i}", heading_style))
            
            # Basic property info
            prop_data = [
                ["Address", prop.get("formattedAddress", "N/A")],
                ["Property Type", prop.get("propertyType", "N/A")],
                ["Bedrooms", str(prop.get("bedrooms", "N/A"))],
                ["Bathrooms", str(prop.get("bathrooms", "N/A"))],
                ["Square Footage", f"{prop.get('squareFootage', 'N/A'):,}" if prop.get('squareFootage') else "N/A"],
                ["Year Built", str(prop.get("yearBuilt", "N/A"))],
                ["Last Sale Price", f"${prop.get('lastSalePrice', 0):,}" if prop.get('lastSalePrice') else "N/A"],
                ["Owner Occupied", "Yes" if prop.get("ownerOccupied") else "No"]
            ]
            
            prop_table = Table(prop_data, colWidths=[2*inch, 4*inch])
            prop_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            content.append(prop_table)
            content.append(Spacer(1, 15))
            
            # Break page after every 2 properties (except last)
            if i % 2 == 0 and i < len(search_results):
                content.append(Spacer(1, 50))
        
        # Build PDF
        doc.build(content)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"property_report_{search_id or 'export'}_{timestamp}.pdf"
        
        return pdf_bytes, filename
        
    except Exception as e:
        raise Exception(f"PDF export failed: {str(e)}")


def get_export_summary(search_data):
    """
    Get a summary of the search data for export metadata.
    
    Args:
        search_data: Search data dictionary
    
    Returns:
        dict: Summary information
    """
    try:
        summary = {
            "Export Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Total Properties": 0,
            "Search Address": "N/A",
            "Search Date": "N/A"
        }
        
        # Extract search information
        if isinstance(search_data, dict):
            if "property_data" in search_data:
                prop_data = search_data["property_data"]
                
                if "address" in prop_data:
                    summary["Search Address"] = prop_data["address"]
                
                if "search_timestamp" in prop_data:
                    summary["Search Date"] = prop_data["search_timestamp"]
                
                if "results" in prop_data and isinstance(prop_data["results"], list):
                    summary["Total Properties"] = len(prop_data["results"])
            
            elif "results" in search_data and isinstance(search_data["results"], list):
                summary["Total Properties"] = len(search_data["results"])
        
        return summary
        
    except Exception as e:
        return {
            "Export Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Error": f"Could not generate summary: {str(e)}"
        }

