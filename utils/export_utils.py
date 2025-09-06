import csv
import io
import json
from datetime import datetime
import logging
from flask import make_response
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class ExportUtils:
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def export_to_csv(self, keywords_data):
        """Export keywords data to CSV format"""
        try:
            output = io.StringIO()
            
            if not keywords_data:
                # Create empty CSV with headers
                fieldnames = [
                    'keyword', 'search_volume', 'trend_score', 'amazon_results',
                    'competition_score', 'difficulty_score', 'profitability_score',
                    'category', 'avg_price', 'avg_reviews'
                ]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
            else:
                # Flatten the data for CSV export
                flattened_data = []
                for item in keywords_data:
                    flat_item = {
                        'keyword': item.get('keyword', ''),
                        'search_volume': item.get('search_volume', 0),
                        'trend_score': item.get('trend_score', 0.0),
                        'amazon_results': item.get('amazon_results', 0),
                        'competition_score': item.get('competition_score', 0.0),
                        'difficulty_score': item.get('difficulty_score', 0.0),
                        'profitability_score': item.get('profitability_score', 0.0),
                        'category': item.get('category', 'Unknown'),
                        'avg_price': item.get('avg_price', 0.0),
                        'avg_reviews': item.get('avg_reviews', 0),
                        'recommendation': item.get('recommendation', ''),
                        'exported_at': datetime.now().isoformat()
                    }
                    flattened_data.append(flat_item)
                
                if flattened_data:
                    fieldnames = list(flattened_data[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
            
            # Create response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=keywords_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
            
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            return make_response(f"Error creating CSV export: {str(e)}", 500)
    
    def export_to_excel(self, keywords_data):
        """Export keywords data to Excel format"""
        try:
            output = io.BytesIO()
            
            if not keywords_data:
                # Create empty DataFrame with headers
                df = pd.DataFrame(columns=[
                    'keyword', 'search_volume', 'trend_score', 'amazon_results',
                    'competition_score', 'difficulty_score', 'profitability_score',
                    'category', 'avg_price', 'avg_reviews', 'recommendation'
                ])
            else:
                # Flatten the data for Excel export
                flattened_data = []
                for item in keywords_data:
                    flat_item = {
                        'keyword': item.get('keyword', ''),
                        'search_volume': item.get('search_volume', 0),
                        'trend_score': item.get('trend_score', 0.0),
                        'amazon_results': item.get('amazon_results', 0),
                        'competition_score': item.get('competition_score', 0.0),
                        'difficulty_score': item.get('difficulty_score', 0.0),
                        'profitability_score': item.get('profitability_score', 0.0),
                        'category': item.get('category', 'Unknown'),
                        'avg_price': item.get('avg_price', 0.0),
                        'avg_reviews': item.get('avg_reviews', 0),
                        'recommendation': item.get('recommendation', ''),
                        'exported_at': datetime.now().isoformat()
                    }
                    flattened_data.append(flat_item)
                
                df = pd.DataFrame(flattened_data)
            
            # Write to Excel
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Keywords Analysis', index=False)
                
                # Add a summary sheet if we have data
                if keywords_data:
                    summary_data = self.create_summary_stats(keywords_data)
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename=keywords_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
            return response
            
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            # Fallback to CSV if Excel export fails
            return self.export_to_csv(keywords_data)
    
    def export_to_pdf(self, keywords_data):
        """Export keywords data to PDF report"""
        try:
            output = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(output, pagesize=A4)
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            story.append(Paragraph("KDP Keyword Research Report", title_style))
            story.append(Spacer(1, 20))
            
            # Report info
            report_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            report_info += f"Total Keywords Analyzed: {len(keywords_data)}<br/>"
            story.append(Paragraph(report_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            if not keywords_data:
                story.append(Paragraph("No keyword data available for export.", self.styles['Normal']))
            else:
                # Summary statistics
                summary_stats = self.create_summary_stats(keywords_data)
                story.append(Paragraph("Summary Statistics", self.styles['Heading2']))
                
                for stat in summary_stats:
                    story.append(Paragraph(f"<b>{stat['Metric']}:</b> {stat['Value']}", self.styles['Normal']))
                
                story.append(Spacer(1, 20))
                
                # Keywords table
                story.append(Paragraph("Keyword Analysis Results", self.styles['Heading2']))
                story.append(Spacer(1, 10))
                
                # Prepare table data
                table_data = [
                    ['Keyword', 'Search Vol.', 'Difficulty', 'Profitability', 'Amazon Results', 'Recommendation']
                ]
                
                for item in keywords_data[:50]:  # Limit to first 50 for PDF
                    row = [
                        item.get('keyword', '')[:30],  # Truncate long keywords
                        str(item.get('search_volume', 0)),
                        f"{item.get('difficulty_score', 0):.1f}",
                        f"{item.get('profitability_score', 0):.1f}",
                        str(item.get('amazon_results', 0)),
                        item.get('recommendation', '')[:30]  # Truncate long recommendations
                    ]
                    table_data.append(row)
                
                # Create table
                table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                
                # Top opportunities section
                top_opportunities = sorted(
                    keywords_data, 
                    key=lambda x: x.get('profitability_score', 0), 
                    reverse=True
                )[:10]
                
                if top_opportunities:
                    story.append(Spacer(1, 30))
                    story.append(Paragraph("Top 10 Opportunities", self.styles['Heading2']))
                    
                    for i, keyword in enumerate(top_opportunities, 1):
                        opp_text = f"{i}. <b>{keyword.get('keyword', '')}</b> - "
                        opp_text += f"Profitability: {keyword.get('profitability_score', 0):.1f}, "
                        opp_text += f"Difficulty: {keyword.get('difficulty_score', 0):.1f}"
                        story.append(Paragraph(opp_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Create response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=keywords_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            return response
            
        except Exception as e:
            logging.error(f"Error exporting to PDF: {e}")
            # Fallback to CSV if PDF export fails
            return self.export_to_csv(keywords_data)
    
    def create_summary_stats(self, keywords_data):
        """Create summary statistics from keywords data"""
        if not keywords_data:
            return []
        
        try:
            # Calculate statistics
            total_keywords = len(keywords_data)
            
            search_volumes = [item.get('search_volume', 0) for item in keywords_data]
            avg_search_volume = sum(search_volumes) / len(search_volumes) if search_volumes else 0
            
            difficulty_scores = [item.get('difficulty_score', 0) for item in keywords_data]
            avg_difficulty = sum(difficulty_scores) / len(difficulty_scores) if difficulty_scores else 0
            
            profitability_scores = [item.get('profitability_score', 0) for item in keywords_data]
            avg_profitability = sum(profitability_scores) / len(profitability_scores) if profitability_scores else 0
            
            # Count opportunities by level
            high_opportunity = len([k for k in keywords_data if k.get('profitability_score', 0) >= 70])
            medium_opportunity = len([k for k in keywords_data if 50 <= k.get('profitability_score', 0) < 70])
            low_opportunity = len([k for k in keywords_data if k.get('profitability_score', 0) < 50])
            
            summary = [
                {'Metric': 'Total Keywords Analyzed', 'Value': total_keywords},
                {'Metric': 'Average Search Volume', 'Value': f"{avg_search_volume:.0f}"},
                {'Metric': 'Average Difficulty Score', 'Value': f"{avg_difficulty:.1f}"},
                {'Metric': 'Average Profitability Score', 'Value': f"{avg_profitability:.1f}"},
                {'Metric': 'High Opportunity Keywords', 'Value': f"{high_opportunity} ({high_opportunity/total_keywords*100:.1f}%)"},
                {'Metric': 'Medium Opportunity Keywords', 'Value': f"{medium_opportunity} ({medium_opportunity/total_keywords*100:.1f}%)"},
                {'Metric': 'Low Opportunity Keywords', 'Value': f"{low_opportunity} ({low_opportunity/total_keywords*100:.1f}%)"},
            ]
            
            return summary
            
        except Exception as e:
            logging.error(f"Error creating summary stats: {e}")
            return [{'Metric': 'Error', 'Value': 'Could not generate statistics'}]
