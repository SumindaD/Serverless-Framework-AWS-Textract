import json
import boto3
import os

def getJobResults(jobId):

    pages = []

    textract = boto3.client('textract')
    response = textract.get_document_text_detection(JobId=jobId)
    
    pages.append(response)

    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    while(nextToken):

        response = textract.get_document_text_detection(JobId=jobId, NextToken=nextToken)

        pages.append(response)
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

    return pages

def handle(event, context):
    notificationMessage = json.loads(json.dumps(event))['Records'][0]['Sns']['Message']
    
    pdfTextExtractionStatus = json.loads(notificationMessage)['Status']
    pdfTextExtractionJobTag = json.loads(notificationMessage)['JobTag']
    pdfTextExtractionJobId = json.loads(notificationMessage)['JobId']
    pdfTextExtractionDocumentLocation = json.loads(notificationMessage)['DocumentLocation']
    
    pdfTextExtractionS3ObjectName = json.loads(json.dumps(pdfTextExtractionDocumentLocation))['S3ObjectName']
    pdfTextExtractionS3Bucket = json.loads(json.dumps(pdfTextExtractionDocumentLocation))['S3Bucket']
    
    print(pdfTextExtractionJobTag + ' : ' + pdfTextExtractionStatus)
    
    pdfText = ''
    
    if(pdfTextExtractionStatus == 'SUCCEEDED'):
        response = getJobResults(pdfTextExtractionJobId)
        
        for resultPage in response:
            for item in resultPage["Blocks"]:
                if item["BlockType"] == "LINE":
                    pdfText += item["Text"] + '\n'
                    
        s3 = boto3.client('s3')
        
        outputTextFileName = os.path.splitext(pdfTextExtractionS3ObjectName)[0] + '.txt'
        s3.put_object(Body=pdfText, Bucket=pdfTextExtractionS3Bucket, Key=outputTextFileName)