from fastapi import APIRouter, Depends, File, UploadFile

from app.api.auth import require_session
from app.api.deps import SiteContext, get_clock, get_document_parser, get_site_context
from app.api.http_errors import NoFilesError, PayloadTooLargeError, TooManyFilesError
from app.api.schemas.articles import ArticleDetail, ArticleSummary, EventOut
from app.api.schemas.imports import ArticlePaste, UploadFileResult, UploadResponse
from app.api.tags import IMPORT
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser
from app.core.use_cases.import_article import import_from_docx, import_from_paste

router = APIRouter(tags=[IMPORT], dependencies=[Depends(require_session)])

PASTE_MAX_BYTES = 2 * 1024 * 1024
UPLOAD_MAX_FILES = 10
UPLOAD_MAX_FILE_BYTES = 10 * 1024 * 1024
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.post("/articles/upload", status_code=201)
async def upload_articles(
    files: list[UploadFile] = File(default=[]),
    ctx: SiteContext = Depends(get_site_context),
    parser: DocumentParser = Depends(get_document_parser),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> UploadResponse:
    if not files:
        raise NoFilesError
    if len(files) > UPLOAD_MAX_FILES:
        raise TooManyFilesError

    results: list[UploadFileResult] = []
    for f in files:
        filename = f.filename or ""
        content = await f.read()
        if len(content) > UPLOAD_MAX_FILE_BYTES:
            results.append(UploadFileResult(filename=filename, ok=False, code="file_too_large"))
            continue
        if not filename.lower().endswith(".docx") or f.content_type != DOCX_CONTENT_TYPE:
            results.append(
                UploadFileResult(filename=filename, ok=False, code="unsupported_file_type")
            )
            continue
        try:
            article = import_from_docx(filename, content, ctx.repository, parser, clock, actor=uid)
        except Exception:
            results.append(UploadFileResult(filename=filename, ok=False, code="unreadable_file"))
            continue
        results.append(
            UploadFileResult(
                filename=filename,
                ok=True,
                article=ArticleSummary(**article.model_dump()),
                warnings=article.warnings,
            )
        )
    return UploadResponse(results=results)


@router.post("/articles/paste", status_code=201)
def paste_article(
    body: ArticlePaste,
    ctx: SiteContext = Depends(get_site_context),
    parser: DocumentParser = Depends(get_document_parser),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    if len(body.html.encode()) > PASTE_MAX_BYTES:
        raise PayloadTooLargeError
    article = import_from_paste(body.html, ctx.repository, parser, clock, actor=uid)
    events = ctx.repository.list_events(article.id)
    return ArticleDetail(
        **article.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )
