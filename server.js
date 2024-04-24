const express = require('express');
const axios = require('axios').default;
const client = require('./client');
const fs = require('fs');
const path = require('path');
const { PDFParser } = require('pdf2json');
const documentsFolder = './documents';

const app = express();

function readDocumentsFromFolder(folderPath) {
    fs.readdir(folderPath, (err, files) => {
        if (err) {
            console.error('Error reading folder:', err);
            return;
        }

        // Filter out non-PDF files
        const pdfFiles = files.filter(file => path.extname(file).toLowerCase() === '.pdf');

        // Loop through each PDF file
        pdfFiles.forEach(pdfFile => {
            const pdfPath = path.join(folderPath, pdfFile);
            chunkDocument(pdfPath);
        });
    });
}

// Function to chunk down the document into pages
async function chunkDocument(pdfPath) {
    try {
        const dataBuffer = fs.readFileSync(pdfPath);
        const pdfParser = new PDFParser();
        pdfParser.on('pdfParser_dataError', errData => console.error(errData.parserError));
        pdfParser.on('pdfParser_dataReady', pdfData => {
            const numPages = pdfData.formImage.Pages.length;

            // Loop through each page
            for (let pageNum = 0; pageNum < numPages; pageNum++) {
                const pageText = pdfData.formImage.Pages[pageNum].Texts.map(item => decodeURIComponent(item.R[0].T)).join(' ');

                // Store the page content in Redis
                client.hset(pdfPath, `page_${pageNum + 1}`, pageText);
            }

            console.log(`Document ${pdfPath} has been chunked and stored in Redis.`);
        });
        pdfParser.parseBuffer(dataBuffer);
    } catch (error) {
        console.error(`Error processing document ${pdfPath}:`, error);
    }
}

// Call this function once to read the documents
readDocumentsFromFolder(documentsFolder);

app.get('/', async (req, res) => {
    const cache = await client.get('responses');
    if (cache) return res.json(JSON.parse(cache));

    try {
        const { data } = await axios.get("https://response.free.beeceptor.com/response");
        await client.set('responses', JSON.stringify(data));
        await client.expire('responses', 10);
        return res.json(data);
    } catch (error) {
        console.error('Error fetching responses:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Endpoint to re-read documents
app.get('/reread-documents', async (req, res) => {
    readDocumentsFromFolder(documentsFolder);
    return res.json({ message: 'Documents are being re-read.' });
});

app.listen(9000, () => {
    console.log('Server is running on port 9000');
});
