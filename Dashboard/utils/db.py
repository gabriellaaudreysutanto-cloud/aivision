import mimetypes
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

_SCHEMA_READY = False
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_ID = os.getenv("MODEL_ID", "YOLO_BEST")
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "YOLO Product Detection")
DEFAULT_MODEL_VERSION = os.getenv("MODEL_VERSION", "best")
DEFAULT_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", os.path.join(BASE_DIR, "models", "best.pt"))


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "aivisionfinal"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "beatrice630478"),
    )


def ensure_schema(conn):
    global _SCHEMA_READY
    if _SCHEMA_READY or os.getenv("DB_AUTO_INIT", "1") != "1":
        return

    ddl = """
    CREATE TABLE IF NOT EXISTS master_apps (
        id BIGSERIAL PRIMARY KEY,
        app_id TEXT NOT NULL UNIQUE,
        app_name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS master_brands (
        id BIGSERIAL PRIMARY KEY,
        brand_id TEXT NOT NULL UNIQUE,
        app_id TEXT NOT NULL,
        brand_name TEXT NOT NULL,
        brand_group TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS master_products (
        id BIGSERIAL PRIMARY KEY,
        app_id TEXT NOT NULL,
        product_id TEXT NOT NULL UNIQUE,
        product_name TEXT NOT NULL,
        short_name TEXT,
        category TEXT,
        product_type TEXT,
        model_status TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        brand_id TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ,
        product_image TEXT
    );

    CREATE TABLE IF NOT EXISTS master_planograms (
        id BIGSERIAL PRIMARY KEY,
        planogram_id TEXT NOT NULL UNIQUE,
        app_id TEXT NOT NULL,
        name TEXT NOT NULL,
        content TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS master_planogram_items (
        id BIGSERIAL PRIMARY KEY,
        planogram_id TEXT NOT NULL,
        shelf_row INTEGER NOT NULL,
        shelf_column INTEGER NOT NULL,
        expected_count INTEGER NOT NULL DEFAULT 1,
        product_id TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_master_brands_app_id
        ON master_brands(app_id);
    CREATE INDEX IF NOT EXISTS idx_master_products_app_id
        ON master_products(app_id);
    CREATE INDEX IF NOT EXISTS idx_master_products_brand_id
        ON master_products(brand_id);
    ALTER TABLE master_products
        ADD COLUMN IF NOT EXISTS product_image TEXT;
    CREATE INDEX IF NOT EXISTS idx_master_planograms_app_id
        ON master_planograms(app_id);
    CREATE INDEX IF NOT EXISTS idx_master_planogram_items_planogram_id
        ON master_planogram_items(planogram_id);

    CREATE TABLE IF NOT EXISTS uploaded_images (
        id BIGSERIAL PRIMARY KEY,
        image_id TEXT NOT NULL UNIQUE,
        app_id TEXT,
        original_filename TEXT NOT NULL,
        stored_filename TEXT,
        file_path TEXT NOT NULL,
        file_url TEXT,
        mime_type TEXT,
        file_size BIGINT,
        uploaded_by TEXT,
        uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        status TEXT NOT NULL DEFAULT 'UPLOADED',
        CONSTRAINT fk_uploaded_images_app
            FOREIGN KEY (app_id) REFERENCES master_apps(app_id)
    );

    CREATE TABLE IF NOT EXISTS model_versions (
        id BIGSERIAL PRIMARY KEY,
        model_id TEXT NOT NULL UNIQUE,
        model_name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        version_name TEXT NOT NULL,
        description TEXT,
        weights_path TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS inference_runs (
        id BIGSERIAL PRIMARY KEY,
        inference_id TEXT NOT NULL UNIQUE,
        image_id TEXT NOT NULL,
        model_id TEXT NOT NULL,
        app_id TEXT,
        inference_type TEXT NOT NULL DEFAULT 'PRODUCT_DETECTION',
        status TEXT NOT NULL DEFAULT 'PROCESSING',
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMPTZ,
        processing_time_ms INTEGER,
        request_payload JSONB,
        response_payload JSONB,
        error_message TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ,
        CONSTRAINT fk_inference_runs_app
            FOREIGN KEY (app_id) REFERENCES master_apps(app_id),
        CONSTRAINT fk_inference_runs_image
            FOREIGN KEY (image_id) REFERENCES uploaded_images(image_id),
        CONSTRAINT fk_inference_runs_model
            FOREIGN KEY (model_id) REFERENCES model_versions(model_id)
    );

    CREATE INDEX IF NOT EXISTS idx_inference_runs_created_at
        ON inference_runs(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_inference_runs_started_at
        ON inference_runs(started_at DESC);
    CREATE INDEX IF NOT EXISTS idx_uploaded_images_uploaded_at
        ON uploaded_images(uploaded_at DESC);
    """

    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    _SCHEMA_READY = True


def fetch_all(query, params=None):
    conn = get_conn()
    try:
        ensure_schema(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if params is None:
                cur.execute(query)
            else:
                cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()

def execute_query(query, params=None):
    conn = get_conn()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            if params is None:
                cur.execute(query)
            else:
                cur.execute(query, params)
            conn.commit()
    finally:
        conn.close()


def _image_id_for_request(request_id: str) -> str:
    return f"IMG-{request_id}"[:100]


def _file_size(path: str):
    if path and os.path.exists(path):
        return os.path.getsize(path)
    return None


def _safe_app_id(cur, app_id):
    if not app_id:
        return None

    cur.execute(
        "SELECT 1 FROM master_apps WHERE app_id = %s AND deleted_at IS NULL LIMIT 1",
        (app_id,),
    )
    return app_id if cur.fetchone() else None


def save_analysis_result(
    request_id: str,
    payload: dict,
    input_image_path: str = None,
    output_image_path: str = None,
):
    result_body = payload.get("result", payload) if isinstance(payload, dict) else {}
    overview = result_body.get("overview", {}) if isinstance(result_body, dict) else {}
    app_id = payload.get("app_id") if isinstance(payload, dict) else None
    run_at = overview.get("run_at")
    final_output_path = output_image_path or overview.get("output_image_path")
    image_id = _image_id_for_request(request_id)
    original_filename = os.path.basename(input_image_path or "") or f"{request_id}.jpg"
    stored_filename = os.path.basename(input_image_path or "") or original_filename
    mime_type = mimetypes.guess_type(input_image_path or "")[0]
    request_payload = {
        "request_id": request_id,
        "app_id": app_id,
        "planogram_id": overview.get("planogram_id"),
        "input_image_path": input_image_path,
        "output_image_path": final_output_path,
        "pricetag": overview.get("pricetag"),
    }

    conn = get_conn()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            resolved_app_id = _safe_app_id(cur, app_id)

            cur.execute(
                """
                INSERT INTO model_versions (
                    model_id,
                    model_name,
                    model_type,
                    version_name,
                    description,
                    weights_path,
                    is_active,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW())
                ON CONFLICT (model_id) DO UPDATE SET
                    model_name = EXCLUDED.model_name,
                    model_type = EXCLUDED.model_type,
                    version_name = EXCLUDED.version_name,
                    description = EXCLUDED.description,
                    weights_path = EXCLUDED.weights_path,
                    is_active = TRUE,
                    updated_at = NOW()
                """,
                (
                    DEFAULT_MODEL_ID,
                    DEFAULT_MODEL_NAME,
                    "YOLO",
                    DEFAULT_MODEL_VERSION,
                    "Default dashboard object-detection model.",
                    DEFAULT_MODEL_PATH,
                ),
            )

            cur.execute(
                """
                INSERT INTO uploaded_images (
                    image_id,
                    app_id,
                    original_filename,
                    stored_filename,
                    file_path,
                    mime_type,
                    file_size,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'UPLOADED')
                ON CONFLICT (image_id) DO UPDATE SET
                    app_id = EXCLUDED.app_id,
                    original_filename = EXCLUDED.original_filename,
                    stored_filename = EXCLUDED.stored_filename,
                    file_path = EXCLUDED.file_path,
                    mime_type = EXCLUDED.mime_type,
                    file_size = EXCLUDED.file_size,
                    status = EXCLUDED.status
                """,
                (
                    image_id,
                    resolved_app_id,
                    original_filename,
                    stored_filename,
                    input_image_path or "",
                    mime_type,
                    _file_size(input_image_path),
                ),
            )

            cur.execute(
                """
                INSERT INTO inference_runs (
                    inference_id,
                    image_id,
                    model_id,
                    app_id,
                    inference_type,
                    status,
                    started_at,
                    finished_at,
                    request_payload,
                    response_payload,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'PRODUCT_DETECTION',
                    %s,
                    COALESCE(%s::timestamptz, NOW()),
                    COALESCE(%s::timestamptz, NOW()),
                    %s,
                    %s,
                    NOW()
                )
                ON CONFLICT (inference_id) DO UPDATE SET
                    image_id = EXCLUDED.image_id,
                    model_id = EXCLUDED.model_id,
                    app_id = EXCLUDED.app_id,
                    inference_type = EXCLUDED.inference_type,
                    status = EXCLUDED.status,
                    started_at = EXCLUDED.started_at,
                    finished_at = EXCLUDED.finished_at,
                    request_payload = EXCLUDED.request_payload,
                    response_payload = EXCLUDED.response_payload,
                    updated_at = NOW()
                """,
                (
                    request_id,
                    image_id,
                    DEFAULT_MODEL_ID,
                    resolved_app_id,
                    payload.get("status", "unknown") if isinstance(payload, dict) else "unknown",
                    run_at,
                    run_at,
                    Json(request_payload),
                    Json(payload),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_latest_analysis_result():
    rows = fetch_all(
        """
        SELECT
            ir.inference_id AS request_id,
            ir.app_id,
            COALESCE(
                ir.response_payload #>> '{result,overview,planogram_id}',
                ir.request_payload #>> '{planogram_id}'
            ) AS planogram_id,
            ir.status,
            CASE
                WHEN (ir.response_payload #>> '{result,overview,detection_count}') ~ '^[0-9]+$'
                    THEN (ir.response_payload #>> '{result,overview,detection_count}')::integer
                WHEN jsonb_typeof(ir.response_payload #> '{result,detections}') = 'array'
                    THEN jsonb_array_length(ir.response_payload #> '{result,detections}')
                WHEN jsonb_typeof(ir.response_payload -> 'detections') = 'array'
                    THEN jsonb_array_length(ir.response_payload -> 'detections')
                ELSE 0
            END AS detection_count,
            ui.file_path AS input_image_path,
            COALESCE(
                ir.response_payload #>> '{result,overview,output_image_path}',
                ir.request_payload #>> '{output_image_path}'
            ) AS output_image_path,
            COALESCE(ir.finished_at, ir.started_at) AS run_at,
            ir.response_payload AS payload,
            ir.created_at,
            ir.updated_at
        FROM inference_runs ir
        LEFT JOIN uploaded_images ui
            ON ir.image_id = ui.image_id
        ORDER BY ir.created_at DESC
        LIMIT 1
        """
    )
    return dict(rows[0]) if rows else None


def fetch_analysis_results(limit: int = 50):
    rows = fetch_all(
        """
        SELECT
            ir.inference_id AS request_id,
            ir.app_id,
            COALESCE(
                ir.response_payload #>> '{result,overview,planogram_id}',
                ir.request_payload #>> '{planogram_id}'
            ) AS planogram_id,
            ir.status,
            CASE
                WHEN (ir.response_payload #>> '{result,overview,detection_count}') ~ '^[0-9]+$'
                    THEN (ir.response_payload #>> '{result,overview,detection_count}')::integer
                WHEN jsonb_typeof(ir.response_payload #> '{result,detections}') = 'array'
                    THEN jsonb_array_length(ir.response_payload #> '{result,detections}')
                WHEN jsonb_typeof(ir.response_payload -> 'detections') = 'array'
                    THEN jsonb_array_length(ir.response_payload -> 'detections')
                ELSE 0
            END AS detection_count,
            ui.file_path AS input_image_path,
            COALESCE(
                ir.response_payload #>> '{result,overview,output_image_path}',
                ir.request_payload #>> '{output_image_path}'
            ) AS output_image_path,
            COALESCE(ir.finished_at, ir.started_at) AS run_at,
            ir.response_payload AS payload,
            ir.created_at,
            ir.updated_at
        FROM inference_runs ir
        LEFT JOIN uploaded_images ui
            ON ir.image_id = ui.image_id
        ORDER BY ir.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return [dict(row) for row in rows]


def count_analysis_results() -> int:
    rows = fetch_all("SELECT COUNT(*) AS total FROM inference_runs")
    if not rows:
        return 0
    return int(rows[0].get("total") or 0)
