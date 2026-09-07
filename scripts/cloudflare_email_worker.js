/**
 * Cloudflare Email Routing + Worker para Rental Handler (Feature F-21)
 * 
 * Este worker recibe correos dirigidos a facturas@tudominio.com (o cualquier alias configurado),
 * extrae los archivos adjuntos PDF mediante postal-mime y los reenvía de forma segura
 * vía HTTP POST (multipart/form-data) al Webhook de Rental Handler.
 * 
 * Coste: 100% Gratuito en el plan Free de Cloudflare (hasta 100.000 invocaciones/día).
 * 
 * ==============================================================================
 * GUÍA DE DESPLIEGUE EN CLOUDFLARE (Paso a Paso):
 * ==============================================================================
 * 1. Prerrequisitos:
 *    - Tener tu dominio gestionado en Cloudflare (DNS activo).
 *    - Node.js instalado para Wrangler CLI (opcional, o hacerlo desde el Dashboard Web).
 * 
 * 2. Configurar Email Routing en Cloudflare:
 *    - En el panel de Cloudflare, entra a tu dominio -> "Email Routing".
 *    - Haz clic en "Enable Email Routing" (Cloudflare configurará los registros MX y SPF automáticamente).
 * 
 * 3. Crear el Worker:
 *    - En el panel lateral de Cloudflare: "Workers & Pages" -> "Create application" -> "Create Worker".
 *    - Nómbralo: `rental-handler-email-ingest`.
 *    - Pega este archivo en el editor de código.
 *    - Si usas `wrangler`, añade el paquete npm `postal-mime`:
 *        npm install postal-mime
 * 
 * 4. Configurar Variables de Entorno y Secretos:
 *    - En la pestaña "Settings" -> "Variables" del Worker, añade:
 *        - `RENTAL_HANDLER_WEBHOOK_URL`: https://tu-dominio.com/api/webhooks/inbound-email
 *        - `RENTAL_HANDLER_WEBHOOK_SECRET` (como Secret / cifrado): tu clave secreta
 * 
 * 5. Vincular Email Routing con el Worker:
 *    - Vuelve a tu dominio -> "Email Routing" -> "Routing Rules".
 *    - Crea una regla de captura personalizada:
 *        - Match: "Custom address" -> facturas@tudominio.com (o * para catch-all)
 *        - Action: "Send to a Worker" -> Selecciona `rental-handler-email-ingest`.
 *    - Guarda la regla.
 * 
 * ¡Listo! Cualquier correo reenviado por los propietarios a esa dirección se procesará
 * automáticamente y contabilizará sus gastos en Rental Handler de forma inmediata.
 */

import PostalMime from 'postal-mime';

export default {
  /**
   * Handler de eventos de correo entrante de Cloudflare Email Routing.
   * @param {EmailMessage} message
   * @param {Record<string, string>} env
   * @param {ExecutionContext} ctx
   */
  async email(message, env, ctx) {
    try {
      const rawEmail = await new Response(message.raw).arrayBuffer();
      const parser = new PostalMime();
      const parsedEmail = await parser.parse(rawEmail);

      const formData = new FormData();
      formData.append('from', message.from || parsedEmail.from?.address || '');
      formData.append('to', message.to || '');
      formData.append('subject', parsedEmail.subject || '');

      let pdfCount = 0;
      if (parsedEmail.attachments && parsedEmail.attachments.length > 0) {
        for (const att of parsedEmail.attachments) {
          const isPdf = att.mimeType === 'application/pdf' ||
                        (att.filename && att.filename.toLowerCase().endsWith('.pdf'));
          if (isPdf && att.content) {
            const blob = new Blob([att.content], { type: 'application/pdf' });
            formData.append('files', blob, att.filename || `factura_${pdfCount + 1}.pdf`);
            pdfCount++;
          }
        }
      }

      if (pdfCount === 0) {
        console.log(`[Email Worker] Correo de ${message.from} ignorado: sin adjuntos PDF.`);
        return;
      }

      const webhookUrl = env.RENTAL_HANDLER_WEBHOOK_URL || 'http://localhost:8000/api/webhooks/inbound-email';
      const webhookSecret = env.RENTAL_HANDLER_WEBHOOK_SECRET || 'dev-inbound-secret';

      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'X-Webhook-Secret': webhookSecret,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[Email Worker] Error al enviar al webhook (${response.status}): ${errorText}`);
      } else {
        const result = await response.json();
        console.log(`[Email Worker] Procesado con éxito:`, JSON.stringify(result));
      }
    } catch (err) {
      console.error('[Email Worker] Excepción no controlada procesando correo:', err);
    }
  },
};
