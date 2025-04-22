import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class ReceiptGenerator:
    def __init__(self, output_directory="output/receipts"):
        """
        Initialize receipt generator
        
        Args:
            output_directory (str): Directory to save receipts
        """
        self.output_directory = output_directory
        os.makedirs(output_directory, exist_ok=True)
    
    def generate_receipt(self, items, prices, tax_rate=0.07):
        """
        Generate a PDF receipt based on the current items
        
        Args:
            items (dict): Dictionary of items with counts
            prices (dict): Dictionary of prices for each item
            tax_rate (float): Tax rate to apply
            
        Returns:
            str: Path to the generated receipt file
        """
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_directory, f"receipt_{timestamp}.pdf")
        
        # Get current date and time for receipt
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add header
        header = Paragraph("<b>Retail Billing Receipt</b>", styles["Title"])
        elements.append(header)
        
        # Add date and time
        date_time = Paragraph(f"Date: {current_time}", styles["Normal"])
        elements.append(date_time)
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))
        
        # Create data for table
        data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        total_amount = 0
        
        # Add items to the bill
        items_added = False
        for cls_name, item_info in items.items():
            if item_info["count"] > 0:
                items_added = True
                unit_price = prices.get(cls_name, 0)
                total_price = unit_price * item_info["count"]
                total_amount += total_price
                
                data.append([
                    cls_name, 
                    str(item_info["count"]), 
                    f"{unit_price:.2f}", 
                    f"{total_price:.2f}"
                ])
        
        # If no items were added, show a placeholder
        if not items_added:
            print("Warning: No items with count > 0 found")
            data.append(['No items detected', '0', '0.00', '0.00'])
        
        # Add subtotal, tax, and total
        tax_amount = total_amount * tax_rate
        final_total = total_amount + tax_amount
        
        data.append(['', '', 'Subtotal:', f"{total_amount:.2f}"])
        data.append(['', '', f'Tax ({tax_rate*100}%):', f"{tax_amount:.2f}"])
        data.append(['', '', 'Total:', f"{final_total:.2f}"])
        
        # Create table and set style
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Paragraph("<br/><br/>Thank you for shopping with us!", styles["Normal"]))
        
        # Build PDF
        doc.build(elements)
        print(f"Receipt generated: {filename}")
        return filename