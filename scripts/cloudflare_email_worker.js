/**
 * Cloudflare Email Worker - Zero Dependencies Standalone
 * Procesa emails entrantes de Cloudflare Email Routing y reenvía
 * los archivos adjuntos PDF al webhook de FastAPI.
 */

export default {
  async email(message, env, ctx) {
    try {
      const from = message.from || '';
      const to = message.to || '';
      const headers = message.headers;
      const subject = headers ? (headers.get('subject') || '') : '';

      // Leer el contenido MIME completo del email
      const rawEmail = await new Response(message.raw).arrayBuffer();
      
      // Parsear los adjuntos PDF directamente del stream MIME sin librerías externas
      const pdfs = extractPdfAttachments(rawEmail);

      console.log(`Recibido correo de: ${from}, Asunto: "${subject}", PDFs extraídos: ${pdfs.length}`);

      const webhookUrl = env.RENTAL_HANDLER_WEBHOOK_URL;
      const webhookSecret = env.RENTAL_HANDLER_WEBHOOK_SECRET;

      if (!webhookUrl) {
        console.error('ERROR: RENTAL_HANDLER_WEBHOOK_URL no está configurada.');
        return;
      }

      const formData = new FormData();
      formData.append('from', from);
      formData.append('to', to);
      formData.append('subject', subject);

      for (const pdf of pdfs) {
        const blob = new Blob([pdf.data], { type: 'application/pdf' });
        formData.append('files', blob, pdf.filename);
      }

      const requestHeaders = {};
      if (webhookSecret) {
        requestHeaders['X-Webhook-Secret'] = webhookSecret;
      }

      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: requestHeaders,
        body: formData,
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error(`Error enviando al webhook (${response.status}): ${errText}`);
      } else {
        const json = await response.json();
        console.log('Webhook procesado con éxito:', JSON.stringify(json));
      }
    } catch (err) {
      console.error('Error procesando email entrante:', err.message, err.stack);
    }
  }
};

/**
 * Extractor nativo simple y robusto de adjuntos PDF en flujos RFC 2046 MIME
 */
function extractPdfAttachments(arrayBuffer) {
  const textDecoder = new TextDecoder('latin1');
  const rawString = textDecoder.decode(arrayBuffer);
  const pdfs = [];

  // Buscar límites de multipart
  const boundaryMatch = rawString.match(/boundary="?([^";\r\n]+)"?/i);
  if (!boundaryMatch) return pdfs;

  const boundary = boundaryMatch[1];
  const parts = rawString.split(new RegExp(`--${escapeRegExp(boundary)}`));

  for (const part of parts) {
    if (!part || part.startsWith('--')) continue;

    const headerEndIndex = part.indexOf('\r\n\r\n');
    const headerEndAlt = part.indexOf('\n\n');
    const splitIndex = headerEndIndex !== -1 ? headerEndIndex + 4 : (headerEndAlt !== -1 ? headerEndAlt + 2 : -1);

    if (splitIndex === -1) continue;

    const headersText = part.substring(0, splitIndex);
    const bodyText = part.substring(splitIndex);

    const isPdf = /content-type:[^\r\n]*application\/pdf/i.test(headersText) ||
                  /filename="?[^"]*\.pdf"?/i.test(headersText);

    if (!isPdf) continue;

    // Extraer nombre de fichero
    const filenameMatch = headersText.match(/filename="?([^"\r\n]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1].replace(/[\r\n]/g, '').trim() : `factura_${Date.now()}.pdf`;

    // Extraer encoding (usualmente base64)
    const isBase64 = /content-transfer-encoding:[^\r\n]*base64/i.test(headersText);
    
    let pdfBytes;
    if (isBase64) {
      const cleanBase64 = bodyText.replace(/[\r\n\s]/g, '');
      const binaryString = atob(cleanBase64);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      pdfBytes = bytes;
    } else {
      const bytes = new Uint8Array(bodyText.length);
      for (let i = 0; i < bodyText.length; i++) {
        bytes[i] = bodyText.charCodeAt(i);
      }
      pdfBytes = bytes;
    }

    pdfs.push({ filename, data: pdfBytes });
  }

  return pdfs;
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
