-- TenderWise Database Schema - VERSIÓN FINAL CORREGIDA
-- Sin errores de Foreign Key cascade

USE TenderWiseDB;
GO

-- Drop existing objects if they exist (for clean setup)
DROP VIEW IF EXISTS vw_agent_performance;
DROP VIEW IF EXISTS vw_document_analytics;
DROP VIEW IF EXISTS vw_session_analytics;

DROP PROCEDURE IF EXISTS sp_CleanupOldData;
DROP PROCEDURE IF EXISTS sp_GetSessionSummary;
DROP PROCEDURE IF EXISTS sp_LogRiskReport;
DROP PROCEDURE IF EXISTS sp_LogAgentEvent;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS system_config;
DROP TABLE IF EXISTS compliance_validations;
DROP TABLE IF EXISTS contractor_validations;
DROP TABLE IF EXISTS comparison_results;
DROP TABLE IF EXISTS analysis_results;
DROP TABLE IF EXISTS fact_risk_report;
DROP TABLE IF EXISTS dim_agent_event_log;
DROP TABLE IF EXISTS dim_agent_thinking_log;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS sessions;
GO

-- Sessions table - Track user sessions and analysis workflows
CREATE TABLE sessions (
    session_id NVARCHAR(50) PRIMARY KEY,
    user_id NVARCHAR(100) NULL,
    created_timestamp DATETIME2 NOT NULL DEFAULT GETDATE(),
    last_activity DATETIME2 NOT NULL DEFAULT GETDATE(),
    session_status NVARCHAR(20) NOT NULL DEFAULT 'active', -- active, closed, expired
    metadata NVARCHAR(MAX) NULL, -- JSON metadata
    document_count INT NOT NULL DEFAULT 0,
    analysis_count INT NOT NULL DEFAULT 0
);

CREATE INDEX IX_sessions_user_id ON sessions (user_id);
CREATE INDEX IX_sessions_last_activity ON sessions (last_activity);
CREATE INDEX IX_sessions_status ON sessions (session_status);
GO

-- Documents table - Store uploaded tender documents
CREATE TABLE documents (
    document_id NVARCHAR(50) PRIMARY KEY,
    session_id NVARCHAR(50) NOT NULL,
    original_filename NVARCHAR(500) NOT NULL,
    file_path NVARCHAR(1000) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type NVARCHAR(100) NULL,
    document_type NVARCHAR(50) NULL, -- pliego, propuesta, contrato, etc.
    text_length INT NULL,
    upload_timestamp DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_timestamp DATETIME2 NULL,
    analysis_data NVARCHAR(MAX) NULL, -- JSON with extracted data
    validation_result NVARCHAR(MAX) NULL, -- JSON with validation results
    metadata NVARCHAR(MAX) NULL, -- JSON metadata
    processing_status NVARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    is_valid BIT NULL,
    error_message NVARCHAR(MAX) NULL
);

-- Add foreign key constraint separately
ALTER TABLE documents ADD CONSTRAINT FK_documents_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE;

CREATE INDEX IX_documents_session_id ON documents (session_id);
CREATE INDEX IX_documents_type ON documents (document_type);
CREATE INDEX IX_documents_upload_time ON documents (upload_timestamp);
CREATE INDEX IX_documents_status ON documents (processing_status);
GO

-- Agent thinking log - Detailed thinking process tracking
CREATE TABLE dim_agent_thinking_log (
    thinking_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agent_name NVARCHAR(100) NOT NULL,
    thinking_stage NVARCHAR(100) NOT NULL,
    thought_content NVARCHAR(MAX) NULL,
    thinking_stage_output NVARCHAR(MAX) NULL,
    agent_output NVARCHAR(MAX) NULL,
    conversation_id NVARCHAR(50) NULL,
    session_id NVARCHAR(50) NULL,
    azure_agent_id NVARCHAR(100) NULL,
    model_deployment_name NVARCHAR(100) NULL,
    thread_id NVARCHAR(100) NULL,
    user_query NVARCHAR(MAX) NULL,
    status NVARCHAR(50) NOT NULL DEFAULT 'success',
    created_date DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- Add foreign key constraint separately - NO CASCADE para evitar conflictos
ALTER TABLE dim_agent_thinking_log ADD CONSTRAINT FK_thinking_log_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE NO ACTION;

CREATE INDEX IX_thinking_log_agent ON dim_agent_thinking_log (agent_name);
CREATE INDEX IX_thinking_log_conversation ON dim_agent_thinking_log (conversation_id);
CREATE INDEX IX_thinking_log_session ON dim_agent_thinking_log (session_id);
CREATE INDEX IX_thinking_log_date ON dim_agent_thinking_log (created_date);
CREATE INDEX IX_thinking_log_stage ON dim_agent_thinking_log (thinking_stage);
GO

-- Agent event log - High-level agent actions and results
CREATE TABLE dim_agent_event_log (
    log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agent_name NVARCHAR(100) NOT NULL,
    event_time DATETIME2 NOT NULL DEFAULT GETDATE(),
    action NVARCHAR(100) NOT NULL,
    result_summary NVARCHAR(MAX) NULL,
    conversation_id NVARCHAR(50) NULL,
    session_id NVARCHAR(50) NULL,
    user_query NVARCHAR(MAX) NULL,
    agent_output NVARCHAR(MAX) NULL
);

-- Add foreign key constraint separately - NO CASCADE para evitar conflictos
ALTER TABLE dim_agent_event_log ADD CONSTRAINT FK_event_log_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE NO ACTION;

CREATE INDEX IX_event_log_agent ON dim_agent_event_log (agent_name);
CREATE INDEX IX_event_log_conversation ON dim_agent_event_log (conversation_id);
CREATE INDEX IX_event_log_session ON dim_agent_event_log (session_id);
CREATE INDEX IX_event_log_time ON dim_agent_event_log (event_time);
CREATE INDEX IX_event_log_action ON dim_agent_event_log (action);
GO

-- Risk reports - Generated analysis reports
CREATE TABLE fact_risk_report (
    report_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    session_id NVARCHAR(50) NOT NULL,
    conversation_id NVARCHAR(50) NULL,
    filename NVARCHAR(500) NOT NULL,
    blob_url NVARCHAR(1000) NULL,
    report_type NVARCHAR(50) NOT NULL DEFAULT 'comprehensive',
    created_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    file_size BIGINT NULL,
    download_count INT NOT NULL DEFAULT 0
);

-- Add foreign key constraint separately - NO CASCADE para evitar conflictos
ALTER TABLE fact_risk_report ADD CONSTRAINT FK_risk_report_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE NO ACTION;

CREATE INDEX IX_risk_report_session ON fact_risk_report (session_id);
CREATE INDEX IX_risk_report_conversation ON fact_risk_report (conversation_id);
CREATE INDEX IX_risk_report_type ON fact_risk_report (report_type);
CREATE INDEX IX_risk_report_date ON fact_risk_report (created_date);
GO

-- Analysis results - Store structured analysis results
CREATE TABLE analysis_results (
    analysis_id NVARCHAR(50) PRIMARY KEY,
    session_id NVARCHAR(50) NOT NULL,
    conversation_id NVARCHAR(50) NULL,
    document_id NVARCHAR(50) NULL,
    analysis_type NVARCHAR(50) NOT NULL, -- comprehensive, compliance, risk, comparison
    analysis_status NVARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed
    start_time DATETIME2 NOT NULL DEFAULT GETDATE(),
    end_time DATETIME2 NULL,
    results_data NVARCHAR(MAX) NULL, -- JSON with analysis results
    error_message NVARCHAR(MAX) NULL,
    created_by_agent NVARCHAR(100) NULL
);

-- Add foreign key constraints separately - CAMBIO CLAVE: NO CASCADE en sessions
ALTER TABLE analysis_results ADD CONSTRAINT FK_analysis_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE NO ACTION;

ALTER TABLE analysis_results ADD CONSTRAINT FK_analysis_documents 
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE SET NULL;

CREATE INDEX IX_analysis_session ON analysis_results (session_id);
CREATE INDEX IX_analysis_conversation ON analysis_results (conversation_id);
CREATE INDEX IX_analysis_document ON analysis_results (document_id);
CREATE INDEX IX_analysis_type ON analysis_results (analysis_type);
CREATE INDEX IX_analysis_status ON analysis_results (analysis_status);
CREATE INDEX IX_analysis_start_time ON analysis_results (start_time);
GO

-- Comparison results - Store multi-proposal comparison results  
CREATE TABLE comparison_results (
    comparison_id NVARCHAR(50) PRIMARY KEY,
    session_id NVARCHAR(50) NOT NULL,
    proposal_ids NVARCHAR(MAX) NOT NULL, -- JSON array of document IDs
    comparison_matrix NVARCHAR(MAX) NULL, -- JSON with detailed comparison
    winner_proposal_id NVARCHAR(50) NULL,
    created_timestamp DATETIME2 NOT NULL DEFAULT GETDATE(),
    criteria_weights NVARCHAR(MAX) NULL -- JSON with scoring criteria
);

-- Add foreign key constraint separately - NO CASCADE
ALTER TABLE comparison_results ADD CONSTRAINT FK_comparison_sessions 
FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE NO ACTION;

CREATE INDEX IX_comparison_session ON comparison_results (session_id);
CREATE INDEX IX_comparison_date ON comparison_results (created_timestamp);
GO

-- Contractor validation results - Store RUC and contractor verification
CREATE TABLE contractor_validations (
    validation_id NVARCHAR(50) PRIMARY KEY,
    document_id NVARCHAR(50) NOT NULL,
    contractor_ruc NVARCHAR(13) NOT NULL,
    contractor_name NVARCHAR(500) NULL,
    ruc_valid BIT NOT NULL,
    validation_details NVARCHAR(MAX) NULL, -- JSON with validation results
    search_results NVARCHAR(MAX) NULL, -- JSON with search findings
    risk_assessment NVARCHAR(MAX) NULL, -- JSON with risk analysis
    overall_recommendation NVARCHAR(50) NULL, -- approve, conditional, reject
    validated_timestamp DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- Add foreign key constraint separately
ALTER TABLE contractor_validations ADD CONSTRAINT FK_contractor_documents 
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE;

CREATE INDEX IX_contractor_document ON contractor_validations (document_id);
CREATE INDEX IX_contractor_ruc ON contractor_validations (contractor_ruc);
CREATE INDEX IX_contractor_valid ON contractor_validations (ruc_valid);
CREATE INDEX IX_contractor_recommendation ON contractor_validations (overall_recommendation);
GO

-- Compliance validation results - Store LOSNCP compliance checks
CREATE TABLE compliance_validations (
    compliance_id NVARCHAR(50) PRIMARY KEY,
    document_id NVARCHAR(50) NOT NULL,
    overall_compliant BIT NOT NULL,
    financial_compliance NVARCHAR(MAX) NULL, -- JSON with financial validation
    legal_compliance NVARCHAR(MAX) NULL, -- JSON with legal validation
    technical_compliance NVARCHAR(MAX) NULL, -- JSON with technical validation
    violations_count INT NOT NULL DEFAULT 0,
    warnings_count INT NOT NULL DEFAULT 0,
    risk_level NVARCHAR(20) NULL, -- low, medium, high
    validated_timestamp DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- Add foreign key constraint separately
ALTER TABLE compliance_validations ADD CONSTRAINT FK_compliance_documents 
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE;

CREATE INDEX IX_compliance_document ON compliance_validations (document_id);
CREATE INDEX IX_compliance_overall ON compliance_validations (overall_compliant);
CREATE INDEX IX_compliance_risk ON compliance_validations (risk_level);
GO

-- System configuration and settings
CREATE TABLE system_config (
    config_key NVARCHAR(100) PRIMARY KEY,
    config_value NVARCHAR(MAX) NOT NULL,
    config_type NVARCHAR(50) NOT NULL DEFAULT 'string', -- string, number, boolean, json
    description NVARCHAR(500) NULL,
    created_timestamp DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_timestamp DATETIME2 NULL
);

-- Audit log for system events
CREATE TABLE audit_log (
    audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    event_type NVARCHAR(100) NOT NULL,
    event_description NVARCHAR(MAX) NULL,
    user_id NVARCHAR(100) NULL,
    session_id NVARCHAR(50) NULL,
    entity_type NVARCHAR(100) NULL, -- session, document, analysis, etc.
    entity_id NVARCHAR(50) NULL,
    old_values NVARCHAR(MAX) NULL, -- JSON
    new_values NVARCHAR(MAX) NULL, -- JSON
    timestamp DATETIME2 NOT NULL DEFAULT GETDATE(),
    ip_address NVARCHAR(50) NULL,
    user_agent NVARCHAR(500) NULL
);

CREATE INDEX IX_audit_timestamp ON audit_log (timestamp);
CREATE INDEX IX_audit_event_type ON audit_log (event_type);
CREATE INDEX IX_audit_user ON audit_log (user_id);
CREATE INDEX IX_audit_session ON audit_log (session_id);
CREATE INDEX IX_audit_entity ON audit_log (entity_type, entity_id);
GO

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('app_version', '1.0.0', 'string', 'Application version'),
('max_file_size_mb', '50', 'number', 'Maximum file size in MB'),
('session_timeout_hours', '24', 'number', 'Session timeout in hours'),
('cleanup_days', '30', 'number', 'Days to keep old data'),
('analysis_timeout_minutes', '10', 'number', 'Analysis timeout in minutes'),
('max_concurrent_analyses', '5', 'number', 'Maximum concurrent analyses'),
('enable_contractor_search', 'true', 'boolean', 'Enable contractor web search'),
('default_language', 'es', 'string', 'Default system language');
GO

-- Create stored procedures for common operations

-- Procedure to log agent events
CREATE PROCEDURE sp_LogAgentEvent
    @agent_name NVARCHAR(100),
    @action NVARCHAR(100),
    @result_summary NVARCHAR(MAX) = NULL,
    @conversation_id NVARCHAR(50) = NULL,
    @session_id NVARCHAR(50) = NULL,
    @user_query NVARCHAR(MAX) = NULL,
    @agent_output NVARCHAR(MAX) = NULL
AS
BEGIN
    INSERT INTO dim_agent_event_log (
        agent_name, action, result_summary, conversation_id, 
        session_id, user_query, agent_output
    )
    VALUES (
        @agent_name, @action, @result_summary, @conversation_id,
        @session_id, @user_query, @agent_output
    );
END;
GO

-- Procedure to log risk reports
CREATE PROCEDURE sp_LogRiskReport
    @session_id NVARCHAR(50),
    @conversation_id NVARCHAR(50) = NULL,
    @filename NVARCHAR(500),
    @blob_url NVARCHAR(1000) = NULL,
    @report_type NVARCHAR(50) = 'comprehensive',
    @file_size BIGINT = NULL
AS
BEGIN
    INSERT INTO fact_risk_report (
        session_id, conversation_id, filename, blob_url, report_type, file_size
    )
    VALUES (
        @session_id, @conversation_id, @filename, @blob_url, @report_type, @file_size
    );
END;
GO

-- Procedure to get session summary
CREATE PROCEDURE sp_GetSessionSummary
    @session_id NVARCHAR(50)
AS
BEGIN
    SELECT 
        s.session_id,
        s.created_timestamp,
        s.last_activity,
        s.session_status,
        s.document_count,
        s.analysis_count,
        COUNT(DISTINCT d.document_id) as actual_document_count,
        COUNT(DISTINCT aer.conversation_id) as actual_analysis_count,
        COUNT(DISTINCT frr.report_id) as report_count
    FROM sessions s
    LEFT JOIN documents d ON s.session_id = d.session_id
    LEFT JOIN dim_agent_event_log aer ON s.session_id = aer.session_id
    LEFT JOIN fact_risk_report frr ON s.session_id = frr.session_id
    WHERE s.session_id = @session_id
    GROUP BY s.session_id, s.created_timestamp, s.last_activity, 
             s.session_status, s.document_count, s.analysis_count;
END;
GO

-- Procedure to cleanup old data
CREATE PROCEDURE sp_CleanupOldData
    @days_old INT = 30
AS
BEGIN
    DECLARE @cutoff_date DATETIME2 = DATEADD(day, -@days_old, GETDATE());
    DECLARE @deleted_count INT = 0;
    
    -- Delete old agent thinking logs
    DELETE FROM dim_agent_thinking_log WHERE created_date < @cutoff_date;
    SET @deleted_count = @deleted_count + @@ROWCOUNT;
    
    -- Delete old agent event logs  
    DELETE FROM dim_agent_event_log WHERE event_time < @cutoff_date;
    SET @deleted_count = @deleted_count + @@ROWCOUNT;
    
    -- Delete old audit logs (keep longer)
    DELETE FROM audit_log WHERE timestamp < DATEADD(day, -90, GETDATE());
    SET @deleted_count = @deleted_count + @@ROWCOUNT;
    
    -- Mark old sessions as expired
    UPDATE sessions 
    SET session_status = 'expired' 
    WHERE last_activity < @cutoff_date AND session_status = 'active';
    SET @deleted_count = @deleted_count + @@ROWCOUNT;
    
    SELECT @deleted_count as deleted_records;
END;
GO

-- Create indexes for better performance
CREATE NONCLUSTERED INDEX IX_agent_thinking_compound 
ON dim_agent_thinking_log (agent_name, conversation_id, created_date);

CREATE NONCLUSTERED INDEX IX_agent_event_compound 
ON dim_agent_event_log (session_id, event_time, action);

CREATE NONCLUSTERED INDEX IX_documents_compound 
ON documents (session_id, document_type, upload_timestamp);
GO

-- Create views for reporting

-- View for session analytics
CREATE VIEW vw_session_analytics AS
SELECT 
    s.session_id,
    s.created_timestamp,
    s.last_activity,
    s.session_status,
    COUNT(DISTINCT d.document_id) as document_count,
    COUNT(DISTINCT aer.conversation_id) as analysis_count,
    COUNT(DISTINCT frr.report_id) as report_count,
    DATEDIFF(minute, s.created_timestamp, s.last_activity) as session_duration_minutes,
    MAX(d.upload_timestamp) as last_document_upload,
    MAX(aer.event_time) as last_analysis_activity
FROM sessions s
LEFT JOIN documents d ON s.session_id = d.session_id
LEFT JOIN dim_agent_event_log aer ON s.session_id = aer.session_id
LEFT JOIN fact_risk_report frr ON s.session_id = frr.session_id
GROUP BY s.session_id, s.created_timestamp, s.last_activity, s.session_status;
GO

-- View for document analytics
CREATE VIEW vw_document_analytics AS
SELECT 
    d.document_type,
    COUNT(*) as total_documents,
    AVG(CAST(d.file_size AS FLOAT)) as avg_file_size,
    AVG(CAST(d.text_length AS FLOAT)) as avg_text_length,
    SUM(CASE WHEN d.is_valid = 1 THEN 1 ELSE 0 END) as valid_documents,
    SUM(CASE WHEN d.processing_status = 'completed' THEN 1 ELSE 0 END) as processed_documents,
    MIN(d.upload_timestamp) as first_upload,
    MAX(d.upload_timestamp) as latest_upload
FROM documents d
GROUP BY d.document_type;
GO

-- View for agent performance
CREATE VIEW vw_agent_performance AS
SELECT 
    agent_name,
    COUNT(*) as total_events,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT conversation_id) as unique_conversations,
    MIN(event_time) as first_activity,
    MAX(event_time) as latest_activity
FROM dim_agent_event_log
GROUP BY agent_name;
GO

PRINT 'TenderWise database schema created successfully!';
PRINT 'Tables created: sessions, documents, dim_agent_thinking_log, dim_agent_event_log, fact_risk_report, analysis_results, comparison_results, contractor_validations, compliance_validations, system_config, audit_log';
PRINT 'Stored procedures created: sp_LogAgentEvent, sp_LogRiskReport, sp_GetSessionSummary, sp_CleanupOldData';
PRINT 'Views created: vw_session_analytics, vw_document_analytics, vw_agent_performance';

-- Test basic functionality
INSERT INTO sessions (session_id, user_id, session_status) 
VALUES ('test-session-002', 'setup-test-final', 'active');

SELECT 'Database setup completed successfully - NO CASCADE CONFLICTS!' as status;