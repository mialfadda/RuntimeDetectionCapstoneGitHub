import os
import csv
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


# ─── PDF REPORT GENERATOR ───────────────────────────────────
def generate_pdf_report(prediction, report_path):
    """
    Generates a PDF report for a single prediction.

    Args:
        prediction: Prediction object from database
        report_path: where to save the PDF file
    """
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph('Malicious Website Detection Report', styles['Title']))
    elements.append(Spacer(1, 20))

    # Report metadata
    elements.append(Paragraph(f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC', styles['Normal']))
    elements.append(Paragraph(f'Report ID: {prediction.predictionID}', styles['Normal']))
    elements.append(Spacer(1, 20))

    # Detection result
    elements.append(Paragraph('Detection Result', styles['Heading2']))
    threat_color = colors.red if prediction.label == 'phishing' else colors.green

    result_data = [
        ['Field', 'Value'],
        ['Label', prediction.label.upper()],
        ['Confidence', f'{prediction.confidence}%'],
        ['Inference Time', f'{prediction.inferenceTime}ms' if prediction.inferenceTime else 'N/A'],
        ['Scan Time', prediction.sandboxSession.startTime.strftime(
            '%Y-%m-%d %H:%M:%S') if prediction.sandboxSession.startTime else 'N/A'],
    ]

    result_table = Table(result_data, colWidths=[200, 300])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (1, 1), (1, 1), threat_color),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(result_table)
    elements.append(Spacer(1, 20))

    # Model info
    elements.append(Paragraph('Model Information', styles['Heading2']))
    model_data = [
        ['Field', 'Value'],
        ['Model Name', prediction.modelVersion.model.name if prediction.modelVersion else 'N/A'],
        ['Version', prediction.modelVersion.versionTag if prediction.modelVersion else 'N/A'],
        ['Accuracy',
         f'{prediction.modelVersion.accuracy}%' if prediction.modelVersion and prediction.modelVersion.accuracy else 'N/A'],
    ]

    model_table = Table(model_data, colWidths=[200, 300])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(model_table)

    # Build PDF
    doc.build(elements)
    return report_path


# ─── CSV REPORT GENERATOR ───────────────────────────────────
def generate_csv_report(predictions, report_path):
    """
    Generates a CSV report for multiple predictions.

    Args:
        predictions: list of Prediction objects
        report_path: where to save the CSV file
    """
    with open(report_path, 'w', newline='') as csvfile:
        fieldnames = [
            'prediction_id',
            'label',
            'confidence',
            'inference_time',
            'model_name',
            'model_version',
            'scan_time',
            'threat_level'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for prediction in predictions:
            writer.writerow({
                'prediction_id': prediction.predictionID,
                'label': prediction.label,
                'confidence': f'{prediction.confidence}%',
                'inference_time': f'{prediction.inferenceTime}ms' if prediction.inferenceTime else 'N/A',
                'model_name': prediction.modelVersion.model.name if prediction.modelVersion else 'N/A',
                'model_version': prediction.modelVersion.versionTag if prediction.modelVersion else 'N/A',
                'scan_time': prediction.sandboxSession.startTime.strftime(
                    '%Y-%m-%d %H:%M:%S') if prediction.sandboxSession and prediction.sandboxSession.startTime else 'N/A',
                'threat_level': 'HIGH' if prediction.label == 'phishing' else 'LOW'
            })

    return report_path


# ─── AGGREGATE DETECTION DATA ───────────────────────────────
def aggregate_detection_data(predictions):
    """
    Aggregates detection statistics from a list of predictions.
    Returns a summary dictionary.
    """
    if not predictions:
        return {}

    total = len(predictions)
    phishing_count = sum(1 for p in predictions if p.label == 'phishing')
    legitimate_count = total - phishing_count
    avg_confidence = sum(p.confidence for p in predictions) / total

    high_confidence = sum(1 for p in predictions if p.confidence >= 90)
    low_confidence = sum(1 for p in predictions if p.confidence < 70)

    return {
        'total_scans': total,
        'phishing_detected': phishing_count,
        'legitimate_detected': legitimate_count,
        'phishing_rate': round((phishing_count / total) * 100, 2),
        'average_confidence': round(avg_confidence, 2),
        'high_confidence_scans': high_confidence,
        'low_confidence_scans': low_confidence,
        'generated_at': datetime.utcnow().isoformat()
    }


# ─── SAVE REPORT TO DATABASE ────────────────────────────────
def save_report_to_db(db, Reports, prediction_id, format, file_path, summary_data):
    """
    Saves a generated report record to the database.
    """
    report = Reports(
        predictionID=prediction_id,
        format=format,
        status='complete',
        threatLevel='high' if summary_data.get('phishing_rate', 0) > 50 else 'low',
        summary=json.dumps(summary_data),
        generationTime=datetime.utcnow()
    )
    db.session.add(report)
    db.session.commit()
    return report