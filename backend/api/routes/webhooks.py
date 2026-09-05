"""
Router de Webhooks para la API de Rental Handler.

Provee endpoints para recepción asíncrona de eventos externos, como
la ingesta de facturas por correo electrónico vía Cloudflare Workers (F-21).
"""

from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, Header, Form, File, UploadFile
from backend.api.dependencies import get_process_inbound_email_use_case
from backend.api.schemas import InboundEmailWebhookResponse, InboundEmailItemResultSchema
from backend.application.use_cases import ProcessInboundEmailUseCase

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/inbound-email", response_model=InboundEmailWebhookResponse)
async def inbound_email_webhook(
    from_field: str | None = Form(None, alias="from"),
    sender: str | None = Form(None),
    to_field: str | None = Form(None, alias="to"),
    recipient: str | None = Form(None),
    subject: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    attachments: list[UploadFile] = File(default=[]),
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
    use_case: ProcessInboundEmailUseCase = Depends(get_process_inbound_email_use_case),
):
    """Webhook para ingesta automática de facturas enviadas o reenviadas por correo electrónico (F-21).

    Seguridad:
    - Requiere cabecera 'X-Webhook-Secret' coincidente con la variable INBOUND_WEBHOOK_SECRET.
    - Anti-Spoofing: Solo procesa correos cuyo remitente esté registrado o autorizado en la plataforma.
    - Aislamiento de CUPS: El CUPS de la factura solo se busca en las propiedades pertenecientes al remitente.
    """
    configured_secret = os.getenv("INBOUND_WEBHOOK_SECRET", "dev-inbound-secret")
    if configured_secret and x_webhook_secret != configured_secret:
        raise HTTPException(
            status_code=401,
            detail="Cabecera X-Webhook-Secret ausente o no válida.",
        )

    sender_val = from_field or sender or ""
    recipient_val = to_field or recipient or ""

    # Unificar ficheros recibidos
    all_uploads = list(files) + [a for a in attachments if a not in files]
    file_tuples: list[tuple[str, bytes]] = []

    for upload in all_uploads:
        content = await upload.read()
        filename = upload.filename or "factura.pdf"
        file_tuples.append((filename, content))

    result = use_case.execute(
        sender=sender_val,
        recipient=recipient_val,
        subject=subject,
        attachments=file_tuples,
    )

    items_schema = [
        InboundEmailItemResultSchema(
            filename=item.filename,
            status=item.status,
            property_name=item.property_name,
            cups=item.cups,
            amount=item.amount,
            message=item.message,
        )
        for item in result.items
    ]

    return InboundEmailWebhookResponse(
        status=result.status,
        sender=result.sender,
        recipient=result.recipient,
        subject=result.subject,
        total_attachments=result.total_attachments,
        processed_count=result.processed_count,
        duplicate_count=result.duplicate_count,
        error_count=result.error_count,
        items=items_schema,
        message=result.message,
    )
