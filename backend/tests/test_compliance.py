"""Tests for compliance validation functionality."""

import pytest
import json
from datetime import datetime
from plugins.compliance_validation_plugin import ComplianceValidationPlugin

class TestComplianceValidation:
    """Test suite for LOSNCP compliance validation."""
    
    @pytest.fixture
    def compliance_plugin(self):
        """Create compliance validation plugin instance."""
        return ComplianceValidationPlugin()
    
    @pytest.fixture
    def valid_contract_data(self):
        """Sample valid contract data for testing."""
        return {
            "aspectos_economicos": {
                "monto_total": 20000000.00,
                "monto_sin_iva": 17857142.86,
                "anticipo_porcentaje": 30,
                "anticipo_monto": 6000000.00,
                "forma_pago": "Avances mensuales según cronograma"
            },
            "garantias": [
                {
                    "tipo": "Garantía de fiel cumplimiento",
                    "porcentaje": 5,
                    "monto": 1000000.00,
                    "vigencia": "Hasta recepción provisional",
                    "emisor": "Banco del Pacífico"
                },
                {
                    "tipo": "Garantía de anticipo",
                    "porcentaje": 30,
                    "monto": 6000000.00,
                    "vigencia": "Hasta amortización",
                    "emisor": "Seguros Equinoccial"
                },
                {
                    "tipo": "Garantía por vicios ocultos",
                    "porcentaje": 5,
                    "monto": 1000000.00,
                    "vigencia": "12 meses",
                    "emisor": "Banco Pichincha"
                }
            ],
            "multas_penalizaciones": {
                "retraso_porcentaje_diario": 0.1,
                "penalizacion_tecnica_max": 10,
                "causales_terminacion": [
                    "Abandono de obra",
                    "Incumplimiento grave",
                    "Falsedad documental"
                ]
            },
            "proyecto": {
                "nombre": "Ampliación de la Vía Samborondón",
                "descripcion": "Asfaltado completo de 10 carriles",
                "ubicacion": "Samborondón, Guayas"
            },
            "contratista": {
                "razon_social": "EDIFIKA S.A.",
                "ruc": "0992881364001",
                "representante_legal": "Juan Pérez"
            }
        }
    
    @pytest.fixture 
    def invalid_contract_data(self):
        """Sample invalid contract data for testing."""
        return {
            "aspectos_economicos": {
                "monto_total": 20000000.00,
                "anticipo_porcentaje": 35,  # Exceeds 30% limit
                "anticipo_monto": 7000000.00,
                "forma_pago": "Pago único al final"
            },
            "garantias": [
                {
                    "tipo": "Garantía de fiel cumplimiento",
                    "porcentaje": 3,  # Below 5% minimum
                    "monto": 600000.00
                }
            ],
            "multas_penalizaciones": {
                "retraso_porcentaje_diario": 1.5,  # Exceeds 1% limit
                "causales_terminacion": []
            }
        }
    
    def test_valid_financial_compliance(self, compliance_plugin, valid_contract_data):
        """Test validation of compliant financial terms."""
        contract_json = json.dumps(valid_contract_data)
        
        result = compliance_plugin.validate_financial_compliance(contract_json)
        result_data = json.loads(result)
        
        assert result_data["overall_compliance"] is True
        assert len(result_data["violations"]) == 0
        assert "advance_payment" in result_data["validations"]
        assert "guarantees" in result_data["validations"]
        assert "penalties" in result_data["validations"]
    
    def test_invalid_financial_compliance(self, compliance_plugin, invalid_contract_data):
        """Test validation of non-compliant financial terms."""
        contract_json = json.dumps(invalid_contract_data)
        
        result = compliance_plugin.validate_financial_compliance(contract_json)
        result_data = json.loads(result)
        
        assert result_data["overall_compliance"] is False
        assert len(result_data["violations"]) > 0
        
        # Check specific violations
        violations = result_data["violations"]
        violation_text = " ".join(violations)
        
        assert "35%" in violation_text  # Advance percentage violation
        assert "3%" in violation_text   # Guarantee percentage violation
        assert "1.5%" in violation_text # Penalty percentage violation
    
    def test_advance_payment_validation(self, compliance_plugin):
        """Test specific advance payment validation logic."""
        # Test valid advance (30%)
        contract_data = {
            "aspectos_economicos": {
                "monto_total": 1000000.00,
                "anticipo_porcentaje": 30,
                "anticipo_monto": 300000.00
            },
            "garantias": [],
            "multas_penalizaciones": {}
        }
        
        result = compliance_plugin.validate_financial_compliance(json.dumps(contract_data))
        result_data = json.loads(result)
        
        advance_validation = result_data["validations"]["advance_payment"]
        assert advance_validation["compliant"] is True
        
        # Test invalid advance (35%)
        contract_data["aspectos_economicos"]["anticipo_porcentaje"] = 35
        contract_data["aspectos_economicos"]["anticipo_monto"] = 350000.00
        
        result = compliance_plugin.validate_financial_compliance(json.dumps(contract_data))
        result_data = json.loads(result)
        
        advance_validation = result_data["validations"]["advance_payment"]
        assert advance_validation["compliant"] is False
    
    def test_guarantees_validation(self, compliance_plugin):
        """Test guarantees validation logic."""
        contract_data = {
            "aspectos_economicos": {
                "monto_total": 1000000.00,
                "anticipo_monto": 300000.00
            },
            "garantias": [
                {
                    "tipo": "Garantía de fiel cumplimiento",
                    "porcentaje": 5,
                    "monto": 50000.00
                },
                {
                    "tipo": "Garantía por vicios ocultos",
                    "porcentaje": 5,
                    "monto": 50000.00
                }
            ],
            "multas_penalizaciones": {}
        }
        
        result = compliance_plugin.validate_financial_compliance(json.dumps(contract_data))
        result_data = json.loads(result)
        
        guarantees_validation = result_data["validations"]["guarantees"]
        assert guarantees_validation["compliant"] is True
    
    def test_contract_completeness(self, compliance_plugin, valid_contract_data):
        """Test contract completeness validation."""
        contract_json = json.dumps(valid_contract_data)
        
        result = compliance_plugin.validate_contract_completeness(contract_json)
        result_data = json.loads(result)
        
        assert result_data["overall_complete"] is True
        assert len(result_data["missing_clauses"]) == 0
        assert len(result_data["present_clauses"]) > 0
        
        # Check specific clause analysis
        clause_analysis = result_data["clause_analysis"]
        assert "objeto_contrato" in clause_analysis
        assert "monto_total" in clause_analysis
        assert "garantias" in clause_analysis
    
    def test_comprehensive_compliance_report(self, compliance_plugin, valid_contract_data):
        """Test comprehensive compliance report generation."""
        contract_json = json.dumps(valid_contract_data)
        
        # Get individual validations
        financial_result = compliance_plugin.validate_financial_compliance(contract_json)
        completeness_result = compliance_plugin.validate_contract_completeness(contract_json)
        
        # Generate comprehensive report
        report_result = compliance_plugin.generate_compliance_report(
            financial_result, completeness_result
        )
        report_data = json.loads(report_result)
        
        assert "compliance_report" in report_data
        assert "financial_compliance" in report_data
        assert "contract_completeness" in report_data
        assert "risk_assessment" in report_data
        assert "recommendations" in report_data
        assert "legal_references" in report_data
        
        # Check report structure
        compliance_report = report_data["compliance_report"]
        assert "report_id" in compliance_report
        assert "generation_date" in compliance_report
        assert "regulatory_framework" in compliance_report
        assert compliance_report["regulatory_framework"] == "LOSNCP Ecuador"
    
    def test_specific_losncp_articles(self, compliance_plugin, valid_contract_data):
        """Test validation of specific LOSNCP articles."""
        contract_json = json.dumps(valid_contract_data)
        
        # Test Article 69 (Advance payments)
        article_69_result = compliance_plugin.validate_losncp_article(contract_json, "69")
        article_69_data = json.loads(article_69_result)
        
        assert article_69_data["article_number"] == "69"
        assert article_69_data["compliant"] is True
        assert "legal_text" in article_69_data
        
        # Test Article 74 (Performance guarantee)
        article_74_result = compliance_plugin.validate_losncp_article(contract_json, "74")
        article_74_data = json.loads(article_74_result)
        
        assert article_74_data["article_number"] == "74"
        assert article_74_data["compliant"] is True
    
    def test_mathematical_consistency(self, compliance_plugin):
        """Test mathematical consistency validation."""
        # Test inconsistent amounts
        contract_data = {
            "aspectos_economicos": {
                "monto_total": 1000000.00,
                "anticipo_porcentaje": 30,
                "anticipo_monto": 250000.00  # Should be 300000.00
            },
            "garantias": [
                {
                    "tipo": "Garantía de fiel cumplimiento",
                    "porcentaje": 5,
                    "monto": 40000.00  # Should be 50000.00
                }
            ],
            "multas_penalizaciones": {}
        }
        
        result = compliance_plugin.validate_financial_compliance(json.dumps(contract_data))
        result_data = json.loads(result)
        
        math_validation = result_data["validations"]["mathematical_consistency"]
        assert math_validation["compliant"] is False
        assert len(math_validation["warnings"]) > 0
    
    def test_edge_cases(self, compliance_plugin):
        """Test edge cases and error handling."""
        # Test empty contract data
        empty_result = compliance_plugin.validate_financial_compliance("{}")
        empty_data = json.loads(empty_result)
        assert empty_data["overall_compliance"] is False
        
        # Test malformed JSON
        malformed_result = compliance_plugin.validate_financial_compliance("invalid json")
        malformed_data = json.loads(malformed_result)
        assert "error" in malformed_data
        
        # Test missing required fields
        minimal_data = {"aspectos_economicos": {"monto_total": 1000000}}
        minimal_result = compliance_plugin.validate_financial_compliance(json.dumps(minimal_data))
        minimal_parsed = json.loads(minimal_result)
        assert minimal_parsed["overall_compliance"] is False

@pytest.mark.asyncio
class TestComplianceIntegration:
    """Integration tests for compliance validation with other components."""
    
    async def test_end_to_end_compliance_validation(self):
        """Test end-to-end compliance validation workflow."""
        # This would test the complete workflow from document upload
        # through compliance validation to report generation
        pass
    
    async def test_compliance_with_document_extraction(self):
        """Test compliance validation with extracted document data."""
        # This would test integration with document extraction results
        pass
    
    async def test_compliance_database_logging(self):
        """Test that compliance results are properly logged to database."""
        # This would test database integration
        pass