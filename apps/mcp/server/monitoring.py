"""
Enhanced monitoring and logging for RAG system health metrics
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from threading import Lock
import os

# Configure structured logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'rag_system.log'), mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class RAGMetrics:
    """RAG system performance metrics"""
    timestamp: datetime
    operation: str  # 'search', 'connection', 'embedding'
    symbol: Optional[str]
    duration_ms: float
    success: bool
    result_count: int
    error_message: Optional[str] = None
    relevance_scores: Optional[List[float]] = None
    timeout_occurred: bool = False
    partial_results: bool = False


@dataclass
class SystemHealthStatus:
    """Overall system health status"""
    timestamp: datetime
    vector_db_connected: bool
    service_key_valid: bool
    total_embeddings: int
    unique_symbols: int
    avg_search_latency_ms: float
    success_rate_24h: float
    error_count_24h: int
    last_error: Optional[str] = None


class RAGSystemMonitor:
    """
    Comprehensive monitoring and health tracking for RAG system
    """
    
    def __init__(self, max_metrics_history: int = 10000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.error_history: deque = deque(maxlen=1000)
        self.performance_stats = defaultdict(list)
        self.lock = Lock()
        
        # Health status tracking
        self.last_health_check = None
        self.health_status = None
        
        logger.info("RAG System Monitor initialized")
    
    def record_search_metrics(
        self,
        symbol: str,
        query: str,
        duration_ms: float,
        success: bool,
        result_count: int,
        relevance_scores: Optional[List[float]] = None,
        error_message: Optional[str] = None,
        timeout_occurred: bool = False,
        partial_results: bool = False
    ):
        """
        Record metrics for a RAG search operation
        
        Args:
            symbol: Stock symbol searched
            query: Search query text
            duration_ms: Search duration in milliseconds
            success: Whether search completed successfully
            result_count: Number of results returned
            relevance_scores: List of relevance scores for results
            error_message: Error message if search failed
            timeout_occurred: Whether operation timed out
            partial_results: Whether only partial results were returned
        """
        with self.lock:
            metrics = RAGMetrics(
                timestamp=datetime.now(),
                operation='search',
                symbol=symbol,
                duration_ms=duration_ms,
                success=success,
                result_count=result_count,
                error_message=error_message,
                relevance_scores=relevance_scores,
                timeout_occurred=timeout_occurred,
                partial_results=partial_results
            )
            
            self.metrics_history.append(metrics)
            
            # Update performance stats
            self.performance_stats['search_durations'].append(duration_ms)
            if len(self.performance_stats['search_durations']) > 1000:
                self.performance_stats['search_durations'] = self.performance_stats['search_durations'][-1000:]
            
            # Log structured metrics
            log_data = {
                'event': 'rag_search',
                'symbol': symbol,
                'query_length': len(query),
                'duration_ms': duration_ms,
                'success': success,
                'result_count': result_count,
                'timeout': timeout_occurred,
                'partial': partial_results
            }
            
            if relevance_scores:
                log_data.update({
                    'avg_relevance': sum(relevance_scores) / len(relevance_scores),
                    'max_relevance': max(relevance_scores),
                    'min_relevance': min(relevance_scores)
                })
            
            if error_message:
                log_data['error'] = error_message
                logger.error(f"RAG search failed: {json.dumps(log_data)}")
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'operation': 'search',
                    'error': error_message,
                    'symbol': symbol
                })
            else:
                logger.info(f"RAG search completed: {json.dumps(log_data)}")
    
    def record_connection_metrics(
        self,
        duration_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Record metrics for database connection operations
        
        Args:
            duration_ms: Connection attempt duration in milliseconds
            success: Whether connection succeeded
            error_message: Error message if connection failed
        """
        with self.lock:
            metrics = RAGMetrics(
                timestamp=datetime.now(),
                operation='connection',
                symbol=None,
                duration_ms=duration_ms,
                success=success,
                result_count=0,
                error_message=error_message
            )
            
            self.metrics_history.append(metrics)
            
            log_data = {
                'event': 'rag_connection',
                'duration_ms': duration_ms,
                'success': success
            }
            
            if error_message:
                log_data['error'] = error_message
                logger.error(f"RAG connection failed: {json.dumps(log_data)}")
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'operation': 'connection',
                    'error': error_message,
                    'symbol': None
                })
            else:
                logger.info(f"RAG connection successful: {json.dumps(log_data)}")
    
    def get_health_status(self, force_refresh: bool = False) -> SystemHealthStatus:
        """
        Get current system health status with caching
        
        Args:
            force_refresh: Force refresh of health status
            
        Returns:
            SystemHealthStatus object with current system health
        """
        now = datetime.now()
        
        # Use cached status if recent (within 30 seconds) and not forcing refresh
        if (not force_refresh and 
            self.last_health_check and 
            self.health_status and
            (now - self.last_health_check).seconds < 30):
            return self.health_status
        
        with self.lock:
            # Calculate metrics from recent history
            cutoff_24h = now - timedelta(hours=24)
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_24h]
            
            # Calculate success rate
            if recent_metrics:
                successful = sum(1 for m in recent_metrics if m.success)
                success_rate = (successful / len(recent_metrics)) * 100
            else:
                success_rate = 0.0
            
            # Calculate average search latency
            search_metrics = [m for m in recent_metrics if m.operation == 'search']
            if search_metrics:
                avg_latency = sum(m.duration_ms for m in search_metrics) / len(search_metrics)
            else:
                avg_latency = 0.0
            
            # Count errors in last 24h
            recent_errors = [e for e in self.error_history if e['timestamp'] >= cutoff_24h]
            error_count = len(recent_errors)
            
            # Get last error
            last_error = recent_errors[-1]['error'] if recent_errors else None
            
            # Get database stats
            vector_db_connected = False
            total_embeddings = 0
            unique_symbols = 0
            service_key_valid = False
            
            try:
                from rag.vectordb import get_vector_db_status
                from server.config import get_config_status
                
                db_status = get_vector_db_status()
                config_status = get_config_status()
                
                vector_db_connected = db_status.get('connected', False)
                service_key_valid = config_status.get('service_key_valid', False)
                
                if 'database_stats' in db_status:
                    stats = db_status['database_stats']
                    total_embeddings = stats.get('total_embeddings', 0)
                    unique_symbols = stats.get('unique_symbols', 0)
                    
            except Exception as e:
                logger.error(f"Error getting database status for health check: {e}")
            
            # Create health status
            self.health_status = SystemHealthStatus(
                timestamp=now,
                vector_db_connected=vector_db_connected,
                service_key_valid=service_key_valid,
                total_embeddings=total_embeddings,
                unique_symbols=unique_symbols,
                avg_search_latency_ms=avg_latency,
                success_rate_24h=success_rate,
                error_count_24h=error_count,
                last_error=last_error
            )
            
            self.last_health_check = now
            
            # Log health status
            health_data = asdict(self.health_status)
            health_data['timestamp'] = health_data['timestamp'].isoformat()
            logger.info(f"RAG system health status: {json.dumps(health_data)}")
            
            return self.health_status
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with performance metrics
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff]
            
            if not recent_metrics:
                return {
                    'period_hours': hours,
                    'total_operations': 0,
                    'message': 'No operations in specified period'
                }
            
            # Separate by operation type
            search_ops = [m for m in recent_metrics if m.operation == 'search']
            connection_ops = [m for m in recent_metrics if m.operation == 'connection']
            
            summary = {
                'period_hours': hours,
                'total_operations': len(recent_metrics),
                'search_operations': len(search_ops),
                'connection_operations': len(connection_ops),
                'overall_success_rate': (sum(1 for m in recent_metrics if m.success) / len(recent_metrics)) * 100
            }
            
            # Search-specific metrics
            if search_ops:
                durations = [m.duration_ms for m in search_ops]
                relevance_scores = []
                for m in search_ops:
                    if m.relevance_scores:
                        relevance_scores.extend(m.relevance_scores)
                
                summary['search_metrics'] = {
                    'avg_duration_ms': sum(durations) / len(durations),
                    'min_duration_ms': min(durations),
                    'max_duration_ms': max(durations),
                    'avg_results_per_search': sum(m.result_count for m in search_ops) / len(search_ops),
                    'timeout_rate': (sum(1 for m in search_ops if m.timeout_occurred) / len(search_ops)) * 100,
                    'partial_results_rate': (sum(1 for m in search_ops if m.partial_results) / len(search_ops)) * 100
                }
                
                if relevance_scores:
                    summary['search_metrics']['avg_relevance_score'] = sum(relevance_scores) / len(relevance_scores)
                    summary['search_metrics']['min_relevance_score'] = min(relevance_scores)
                    summary['search_metrics']['max_relevance_score'] = max(relevance_scores)
            
            # Error analysis
            recent_errors = [e for e in self.error_history if e['timestamp'] >= cutoff]
            if recent_errors:
                error_types = defaultdict(int)
                for error in recent_errors:
                    error_msg = error['error'].lower()
                    if 'timeout' in error_msg:
                        error_types['timeout'] += 1
                    elif 'connection' in error_msg:
                        error_types['connection'] += 1
                    elif 'service key' in error_msg:
                        error_types['authentication'] += 1
                    else:
                        error_types['other'] += 1
                
                summary['error_analysis'] = dict(error_types)
            
            return summary
    
    def get_system_status_indicators(self) -> Dict[str, str]:
        """
        Get simple system status indicators for quick health checks
        
        Returns:
            Dictionary with status indicators (GREEN/YELLOW/RED)
        """
        health = self.get_health_status()
        
        indicators = {}
        
        # Database connectivity
        if health.vector_db_connected:
            indicators['database'] = 'GREEN'
        else:
            indicators['database'] = 'RED'
        
        # Service key configuration
        if health.service_key_valid:
            indicators['authentication'] = 'GREEN'
        else:
            indicators['authentication'] = 'RED'
        
        # Performance
        if health.avg_search_latency_ms < 5000:  # Less than 5 seconds
            indicators['performance'] = 'GREEN'
        elif health.avg_search_latency_ms < 15000:  # Less than 15 seconds
            indicators['performance'] = 'YELLOW'
        else:
            indicators['performance'] = 'RED'
        
        # Success rate
        if health.success_rate_24h >= 95:
            indicators['reliability'] = 'GREEN'
        elif health.success_rate_24h >= 80:
            indicators['reliability'] = 'YELLOW'
        else:
            indicators['reliability'] = 'RED'
        
        # Data availability
        if health.total_embeddings > 1000:
            indicators['data_coverage'] = 'GREEN'
        elif health.total_embeddings > 100:
            indicators['data_coverage'] = 'YELLOW'
        else:
            indicators['data_coverage'] = 'RED'
        
        return indicators
    
    def export_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Export metrics for external monitoring systems
        
        Args:
            hours: Number of hours of metrics to export
            
        Returns:
            List of metric dictionaries
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff]
            
            exported = []
            for metric in recent_metrics:
                exported.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'operation': metric.operation,
                    'symbol': metric.symbol,
                    'duration_ms': metric.duration_ms,
                    'success': metric.success,
                    'result_count': metric.result_count,
                    'error_message': metric.error_message,
                    'timeout_occurred': metric.timeout_occurred,
                    'partial_results': metric.partial_results,
                    'avg_relevance': (sum(metric.relevance_scores) / len(metric.relevance_scores)) if metric.relevance_scores else None
                })
            
            return exported


# Global monitor instance
_monitor = None

def get_rag_monitor() -> RAGSystemMonitor:
    """Get or create the global RAG system monitor"""
    global _monitor
    if _monitor is None:
        _monitor = RAGSystemMonitor()
    return _monitor


def log_search_operation(
    symbol: str,
    query: str,
    start_time: float,
    success: bool,
    result_count: int,
    relevance_scores: Optional[List[float]] = None,
    error_message: Optional[str] = None,
    timeout_occurred: bool = False,
    partial_results: bool = False
):
    """
    Convenience function to log a search operation
    
    Args:
        symbol: Stock symbol searched
        query: Search query text
        start_time: Start time from time.time()
        success: Whether search completed successfully
        result_count: Number of results returned
        relevance_scores: List of relevance scores for results
        error_message: Error message if search failed
        timeout_occurred: Whether operation timed out
        partial_results: Whether only partial results were returned
    """
    duration_ms = (time.time() - start_time) * 1000
    monitor = get_rag_monitor()
    monitor.record_search_metrics(
        symbol=symbol,
        query=query,
        duration_ms=duration_ms,
        success=success,
        result_count=result_count,
        relevance_scores=relevance_scores,
        error_message=error_message,
        timeout_occurred=timeout_occurred,
        partial_results=partial_results
    )


def log_connection_operation(
    start_time: float,
    success: bool,
    error_message: Optional[str] = None
):
    """
    Convenience function to log a connection operation
    
    Args:
        start_time: Start time from time.time()
        success: Whether connection succeeded
        error_message: Error message if connection failed
    """
    duration_ms = (time.time() - start_time) * 1000
    monitor = get_rag_monitor()
    monitor.record_connection_metrics(
        duration_ms=duration_ms,
        success=success,
        error_message=error_message
    )