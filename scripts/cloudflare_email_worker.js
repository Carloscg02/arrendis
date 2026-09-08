/**
 * Cloudflare Email Worker - Zero Dependencies Standalone
 * Procesa emails entrantes de Cloudflare Email Routing:
 * 1. Auto-confirma solicitudes de reenvío de Gmail (Zero-click onboarding).
 * 2. Reenvía facturas PDF al webhook de FastAPI en Oracle Cloud.
 */

// Constantes directas para evitar problemas de resolución de env en Cloudflare
const WEBHOOK_SECRET = "302067091229670529e260dd3b4a67d7181888a571034436";
const WEBHOOK_URL = "https://api.arrendis.com/api/webhooks/inbound-email";

export default {
  async email(message, env, ctx) {
    const from = message.from || '';
    try {
      const to = message.to || '';
      const headers = message.headers;
      const subject = headers ? (headers.get('subject') || '') : '';

      // Leer el contenido MIME completo del email
      const rawEmail = await new Response(message.raw).arrayBuffer();

      // =========================================================================
      // 1. AUTO-CONFIRMACIÓN DE REENVÍO DE GMAIL
      // Si el correo viene de Google para verificar el reenvío, lo auto-confirmamos
      // =========================================================================
      if (
        from.includes('forwarding-noreply@google.com') ||
        subject.includes('Confirmación de reenvío de Gmail') ||
        subject.includes('Gmail Forwarding Confirmation') ||
        subject.includes('reenvío')
      ) {
        console.log(`[Gmail Auto-Verify] Detectado correo de verificación de: ${from}`);
        const verified = await handleGmailAutoConfirmation(rawEmail);
        if (verified) {
          console.log('[Gmail Auto-Verify] Reenvío de Gmail confirmado automáticamente con éxito.');
          return;
        }
      }

      // =========================================================================
      // 2. PROCESAMIENTO DE FACTURAS EN PDF
      // =========================================================================
      const pdfs = extractPdfAttachments(rawEmail);

      if (pdfs.length === 0) {
        console.log('No se encontraron adjuntos PDF en el correo recibido.');
        console.log(`Recibido correo de: ${from}, Asunto: "${subject}", PDFs extraídos: ${pdfs.length}`);
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

      const requestHeaders = {
        'X-Webhook-Secret': WEBHOOK_SECRET,
      };

      const response = await fetch(WEBHOOK_URL, {
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
 * Extrae y confirma automáticamente el enlace de verificación de Gmail
 */
async function handleGmailAutoConfirmation(arrayBuffer) {
  try {
    const textDecoder = new TextDecoder('utf-8');
    let rawString = textDecoder.decode(arrayBuffer);

    // Eliminar saltos de línea suaves de quoted-printable (=\r\n o =\n)
    rawString = rawString.replace(/=\r?\n/g, '');

    // Buscar la URL de verificación de Gmail
    const urlMatch = rawString.match(/https:\/\/(?:mail|mail-settings)\.google\.com\/mail\/vf-[a-zA-Z0-9_-]+/i) ||
                     rawString.match(/https:\/\/(?:mail|mail-settings)\.google\.com\/mail\/[^\s<>"'\r\n]+/i);

    const codeMatch = rawString.match(/(?:código de confirmación|confirmation code):\s*([0-9]+)/i);
    if (codeMatch) {
      console.log(`[Gmail Auto-Verify] Código de confirmación detectado: ${codeMatch[1]}`);
    }

    if (!urlMatch) {
      console.warn('[Gmail Auto-Verify] No se localizó la URL de verificación en el cuerpo del correo.');
      return false;
    }

    const confirmUrl = urlMatch[0];
    console.log(`[Gmail Auto-Verify] Visitando URL de verificación: ${confirmUrl}`);

    // 1. GET a la página de verificación de Google
    const getRes = await fetch(confirmUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
      },
    });

    const html = await getRes.text();

    // 2. Comprobar si Google requiere enviar un formulario POST
    const formMatch = html.match(/<form[^>]*action="([^"]*)"[^>]*>/i);
    let actionUrl = confirmUrl;
    if (formMatch && formMatch[1]) {
      actionUrl = formMatch[1].startsWith('http')
        ? formMatch[1]
        : new URL(formMatch[1], confirmUrl).toString();
    }

    const inputRegex = /<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"[^>]*>/gi;
    const postData = new URLSearchParams();
    let inputMatch;
    while ((inputMatch = inputRegex.exec(html)) !== null) {
      postData.append(inputMatch[1], inputMatch[2]);
    }

    // 3. Ejecutar POST de confirmación
    const postRes = await fetch(actionUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
      },
      body: postData.toString(),
    });

    console.log(`[Gmail Auto-Verify] Confirmación enviada a Google (HTTP ${postRes.status})`);
    return true;
  } catch (e) {
    console.error(`[Gmail Auto-Verify] Error procesando verificación: ${e.message}`);
    return false;
  }
}

/**
 * Extractor nativo de adjuntos PDF en flujos RFC 2046 MIME
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
        pdfBytes[i] = bodyText.charCodeAt(i);
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
