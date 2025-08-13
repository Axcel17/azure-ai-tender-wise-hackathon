-- CORRECCIÓN para sp_GetSessionPerformanceMetrics
-- Ejecutar SOLO este procedimiento para reemplazar el problemático

USE TenderWiseDB;
GO

-- Drop and recreate the problematic procedure
DROP PROCEDURE IF EXISTS sp_GetSessionPerformanceMetrics;
GO

-- Procedure to get session performance metrics - CORREGIDO
CREATE PROCEDURE sp_GetSessionPerformanceMetrics
    @session_id NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Simplified approach without nested aggregations
    WITH SessionMetrics AS (
        SELECT 
            s.session_id,
            s.created_timestamp,
            s.last_activity,
            DATEDIFF(minute, s.created_timestamp, s.last_activity) as session_duration_minutes,
            COUNT(DISTINCT d.document_id) as document_count,
            COUNT(DISTINCT aer.conversation_id) as analysis_count,
            COUNT(DISTINCT frr.report_id) as report_count,
            SUM(ISNULL(d.file_size, 0)) / (1024 * 1024) as total_storage_mb
        FROM sessions s
        LEFT JOIN documents d ON s.session_id = d.session_id
        LEFT JOIN dim_agent_event_log aer ON s.session_id = aer.session_id
        LEFT JOIN fact_risk_report frr ON s.session_id = frr.session_id
        WHERE (@session_id IS NULL OR s.session_id = @session_id)
        GROUP BY s.session_id, s.created_timestamp, s.last_activity
    ),
    ProcessingTimes AS (
        SELECT 
            s.session_id,
            AVG(CASE 
                WHEN d.document_id IS NOT NULL THEN 
                    DATEDIFF(second, d.upload_timestamp, ISNULL(s.last_activity, d.upload_timestamp))
                ELSE 0 
            END) as avg_processing_time_seconds
        FROM sessions s
        LEFT JOIN documents d ON s.session_id = d.session_id
        WHERE (@session_id IS NULL OR s.session_id = @session_id)
        GROUP BY s.session_id
    )
    SELECT 
        sm.*,
        ISNULL(pt.avg_processing_time_seconds, 0) as avg_processing_time_seconds,
        CASE 
            WHEN sm.session_duration_minutes < 10 THEN 'Quick Session'
            WHEN sm.session_duration_minutes < 60 THEN 'Standard Session'
            WHEN sm.session_duration_minutes < 240 THEN 'Extended Session'
            ELSE 'Long Session'
        END as session_category,
        CASE 
            WHEN ISNULL(pt.avg_processing_time_seconds, 0) < 30 THEN 'Fast Processing'
            WHEN ISNULL(pt.avg_processing_time_seconds, 0) < 120 THEN 'Standard Processing'
            ELSE 'Slow Processing'
        END as processing_category
    FROM SessionMetrics sm
    LEFT JOIN ProcessingTimes pt ON sm.session_id = pt.session_id
    ORDER BY sm.created_timestamp DESC;
END;
GO

-- Test the corrected procedure
EXEC sp_GetSessionPerformanceMetrics;

PRINT 'sp_GetSessionPerformanceMetrics corrected successfully!';