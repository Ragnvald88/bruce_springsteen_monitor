"""
Intelligent Proxy Scoring System

ML-based proxy selection that learns from success/failure patterns
to optimize proxy usage and minimize detection.
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProxyMetrics:
    """Detailed metrics for a proxy"""
    proxy_url: str
    provider: str
    location: str
    proxy_type: str  # residential, datacenter, mobile
    
    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    detected_requests: int = 0
    
    # Timing metrics
    avg_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    # Platform-specific success rates
    platform_success: Dict[str, float] = field(default_factory=dict)
    platform_detection: Dict[str, float] = field(default_factory=dict)
    
    # Health metrics
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    health_score: float = 1.0
    
    # Cost tracking
    cost_per_request: float = 0.001  # Default cost
    total_cost: float = 0.0
    
    # ML features
    feature_vector: Optional[np.ndarray] = None
    

@dataclass
class ProxyRequest:
    """Request context for proxy scoring"""
    platform: str
    request_type: str  # browse, api, auth
    priority: str  # high, medium, low
    location_preference: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    

class IntelligentProxyRotator:
    """ML-powered proxy rotation and scoring system"""
    
    def __init__(self, proxy_config: Dict[str, Any]):
        """Initialize intelligent proxy manager"""
        self.proxy_config = proxy_config
        self.proxies: Dict[str, ProxyMetrics] = {}
        self.active_proxies: Dict[str, str] = {}  # session_id -> proxy_url
        
        # ML model for proxy selection
        self.ml_model: Optional[RandomForestClassifier] = None
        self.feature_history: List[Tuple[np.ndarray, bool]] = []
        
        # Performance tracking
        self.request_history: List[Dict[str, Any]] = []
        self.detection_patterns: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize proxies
        self._initialize_proxies()
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._train_ml_model_loop())
        
        logger.info(f"Initialized Intelligent Proxy Rotator with {len(self.proxies)} proxies")
        
    def _initialize_proxies(self) -> None:
        """Initialize proxy pool from configuration"""
        for provider, config in self.proxy_config.items():
            if not config.get('enabled'):
                continue
                
            proxy_list = config.get('proxies', [])
            for proxy_info in proxy_list:
                proxy_url = self._build_proxy_url(proxy_info, config)
                
                metrics = ProxyMetrics(
                    proxy_url=proxy_url,
                    provider=provider,
                    location=proxy_info.get('location', 'unknown'),
                    proxy_type=config.get('type', 'residential'),
                    cost_per_request=config.get('cost_per_request', 0.001)
                )
                
                self.proxies[proxy_url] = metrics
                
    def _build_proxy_url(self, proxy_info: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build proxy URL with authentication"""
        protocol = config.get('protocol', 'http')
        host = proxy_info.get('host')
        port = proxy_info.get('port')
        
        if config.get('auth'):
            username = config['auth'].get('username')
            password = config['auth'].get('password')
            return f"{protocol}://{username}:{password}@{host}:{port}"
        
        return f"{protocol}://{host}:{port}"
        
    async def select_optimal_proxy(
        self,
        request: ProxyRequest,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Select the optimal proxy using ML-based scoring
        
        Args:
            request: Request context
            session_id: Optional session ID for sticky sessions
            
        Returns:
            Proxy URL or None if no suitable proxy
        """
        # Check for sticky session
        if session_id and session_id in self.active_proxies:
            proxy_url = self.active_proxies[session_id]
            if self._is_proxy_healthy(self.proxies[proxy_url]):
                return proxy_url
                
        # Get candidate proxies
        candidates = self._get_candidate_proxies(request)
        
        if not candidates:
            logger.error("No healthy proxies available")
            return None
            
        # Score proxies
        proxy_scores = []
        for proxy_url, metrics in candidates:
            score = self._calculate_proxy_score(metrics, request)
            proxy_scores.append((proxy_url, score))
            
        # Use ML model if trained
        if self.ml_model and len(self.feature_history) > 100:
            proxy_scores = self._ml_rank_proxies(proxy_scores, request)
            
        # Select best proxy with some randomization
        proxy_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Add weighted randomization to avoid always picking the same proxy
        if len(proxy_scores) > 1:
            weights = [score for _, score in proxy_scores[:5]]  # Top 5
            if sum(weights) > 0:
                weights = [w / sum(weights) for w in weights]
                selected_idx = np.random.choice(len(weights), p=weights)
                selected_proxy = proxy_scores[selected_idx][0]
            else:
                selected_proxy = proxy_scores[0][0]
        else:
            selected_proxy = proxy_scores[0][0]
            
        # Track active proxy for session
        if session_id:
            self.active_proxies[session_id] = selected_proxy
            
        logger.debug(f"Selected proxy {selected_proxy} for {request.platform}")
        return selected_proxy
        
    def _get_candidate_proxies(
        self,
        request: ProxyRequest
    ) -> List[Tuple[str, ProxyMetrics]]:
        """Get healthy candidate proxies for request"""
        candidates = []
        
        for proxy_url, metrics in self.proxies.items():
            # Skip unhealthy proxies
            if not self._is_proxy_healthy(metrics):
                continue
                
            # Filter by location if specified
            if request.location_preference:
                if request.location_preference.lower() not in metrics.location.lower():
                    continue
                    
            # Filter by platform compatibility
            if request.platform in metrics.platform_detection:
                if metrics.platform_detection[request.platform] > 0.7:
                    continue  # Skip if high detection rate
                    
            candidates.append((proxy_url, metrics))
            
        return candidates
        
    def _is_proxy_healthy(self, metrics: ProxyMetrics) -> bool:
        """Check if proxy is healthy"""
        # Too many consecutive failures
        if metrics.consecutive_failures > 5:
            return False
            
        # Low health score
        if metrics.health_score < 0.3:
            return False
            
        # Recently failed
        if metrics.last_failure:
            failure_age = datetime.now() - metrics.last_failure
            if failure_age < timedelta(minutes=5) and metrics.consecutive_failures > 2:
                return False
                
        # High detection rate
        if metrics.total_requests > 10:
            detection_rate = metrics.detected_requests / metrics.total_requests
            if detection_rate > 0.5:
                return False
                
        return True
        
    def _calculate_proxy_score(
        self,
        metrics: ProxyMetrics,
        request: ProxyRequest
    ) -> float:
        """Calculate proxy score for request"""
        score = metrics.health_score
        
        # Success rate factor
        if metrics.total_requests > 0:
            success_rate = metrics.successful_requests / metrics.total_requests
            score *= success_rate
            
        # Platform-specific success
        if request.platform in metrics.platform_success:
            platform_score = metrics.platform_success[request.platform]
            score *= (0.5 + 0.5 * platform_score)  # Weight platform success
            
        # Response time factor
        if metrics.avg_response_time > 0:
            # Normalize response time (lower is better)
            time_score = 1.0 / (1.0 + metrics.avg_response_time / 1000)
            score *= time_score
            
        # Location preference bonus
        if request.location_preference:
            if request.location_preference.lower() in metrics.location.lower():
                score *= 1.2
                
        # Proxy type preference
        if request.priority == "high" and metrics.proxy_type == "residential":
            score *= 1.3
        elif request.priority == "low" and metrics.proxy_type == "datacenter":
            score *= 1.1
            
        # Cost factor for non-critical requests
        if request.priority != "high":
            cost_factor = 1.0 / (1.0 + metrics.cost_per_request * 100)
            score *= cost_factor
            
        # Freshness bonus (prefer recently successful)
        if metrics.last_success:
            success_age = (datetime.now() - metrics.last_success).total_seconds()
            freshness = 1.0 / (1.0 + success_age / 3600)  # 1 hour decay
            score *= (0.8 + 0.2 * freshness)
            
        return score
        
    def _ml_rank_proxies(
        self,
        proxy_scores: List[Tuple[str, float]],
        request: ProxyRequest
    ) -> List[Tuple[str, float]]:
        """Use ML model to re-rank proxies"""
        if not self.ml_model:
            return proxy_scores
            
        ml_scores = []
        
        for proxy_url, base_score in proxy_scores:
            metrics = self.proxies[proxy_url]
            features = self._extract_features(metrics, request)
            
            try:
                # Get ML prediction (probability of success)
                ml_prob = self.ml_model.predict_proba([features])[0][1]
                
                # Combine base score with ML prediction
                combined_score = base_score * 0.6 + ml_prob * 0.4
                ml_scores.append((proxy_url, combined_score))
                
            except Exception as e:
                logger.error(f"ML scoring failed: {e}")
                ml_scores.append((proxy_url, base_score))
                
        return ml_scores
        
    def _extract_features(
        self,
        metrics: ProxyMetrics,
        request: ProxyRequest
    ) -> np.ndarray:
        """Extract ML features from proxy metrics and request"""
        features = []
        
        # Proxy features
        features.append(metrics.total_requests)
        features.append(metrics.successful_requests / max(1, metrics.total_requests))
        features.append(metrics.detected_requests / max(1, metrics.total_requests))
        features.append(metrics.avg_response_time)
        features.append(metrics.consecutive_failures)
        features.append(metrics.health_score)
        
        # Platform features
        platform_success = metrics.platform_success.get(request.platform, 0.5)
        platform_detection = metrics.platform_detection.get(request.platform, 0.0)
        features.append(platform_success)
        features.append(platform_detection)
        
        # Proxy type features (one-hot encoding)
        features.append(1.0 if metrics.proxy_type == "residential" else 0.0)
        features.append(1.0 if metrics.proxy_type == "datacenter" else 0.0)
        features.append(1.0 if metrics.proxy_type == "mobile" else 0.0)
        
        # Request features
        features.append(1.0 if request.priority == "high" else 0.0)
        features.append(1.0 if request.request_type == "auth" else 0.0)
        
        # Time features
        hour = datetime.now().hour
        features.append(np.sin(2 * np.pi * hour / 24))  # Cyclic hour encoding
        features.append(np.cos(2 * np.pi * hour / 24))
        
        return np.array(features)
        
    async def record_request_result(
        self,
        proxy_url: str,
        request: ProxyRequest,
        success: bool,
        response_time: float,
        detected: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Record the result of a proxy request"""
        if proxy_url not in self.proxies:
            return
            
        metrics = self.proxies[proxy_url]
        
        # Update basic metrics
        metrics.total_requests += 1
        metrics.total_cost += metrics.cost_per_request
        
        if success:
            metrics.successful_requests += 1
            metrics.last_success = datetime.now()
            metrics.consecutive_failures = 0
        else:
            metrics.failed_requests += 1
            metrics.last_failure = datetime.now()
            metrics.consecutive_failures += 1
            
        if detected:
            metrics.detected_requests += 1
            
        # Update response time
        metrics.response_times.append(response_time)
        if len(metrics.response_times) > 100:
            metrics.response_times = metrics.response_times[-50:]
        metrics.avg_response_time = np.mean(metrics.response_times)
        
        # Update platform-specific metrics
        platform = request.platform
        if platform not in metrics.platform_success:
            metrics.platform_success[platform] = 1.0
            metrics.platform_detection[platform] = 0.0
            
        # Exponential moving average for platform metrics
        alpha = 0.1
        metrics.platform_success[platform] = (
            alpha * (1.0 if success else 0.0) +
            (1 - alpha) * metrics.platform_success[platform]
        )
        metrics.platform_detection[platform] = (
            alpha * (1.0 if detected else 0.0) +
            (1 - alpha) * metrics.platform_detection[platform]
        )
        
        # Update health score
        self._update_health_score(metrics)
        
        # Store for ML training
        features = self._extract_features(metrics, request)
        self.feature_history.append((features, success and not detected))
        
        # Log request
        self.request_history.append({
            'timestamp': datetime.now(),
            'proxy': proxy_url,
            'platform': platform,
            'success': success,
            'detected': detected,
            'response_time': response_time,
            'error': error
        })
        
        # Trim history
        if len(self.request_history) > 10000:
            self.request_history = self.request_history[-5000:]
        if len(self.feature_history) > 10000:
            self.feature_history = self.feature_history[-5000:]
            
    def _update_health_score(self, metrics: ProxyMetrics) -> None:
        """Update proxy health score"""
        if metrics.total_requests == 0:
            metrics.health_score = 1.0
            return
            
        # Base score from success rate
        success_rate = metrics.successful_requests / metrics.total_requests
        health = success_rate
        
        # Penalty for detection
        detection_rate = metrics.detected_requests / metrics.total_requests
        health *= (1.0 - detection_rate)
        
        # Penalty for consecutive failures
        if metrics.consecutive_failures > 0:
            health *= 0.9 ** metrics.consecutive_failures
            
        # Response time factor
        if metrics.avg_response_time > 0:
            # Penalize slow proxies
            if metrics.avg_response_time > 5000:  # >5 seconds
                health *= 0.7
            elif metrics.avg_response_time > 2000:  # >2 seconds
                health *= 0.85
                
        # Ensure bounds
        metrics.health_score = max(0.0, min(1.0, health))
        
    async def _health_check_loop(self) -> None:
        """Background task to check proxy health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Test random sample of proxies
                sample_size = min(10, len(self.proxies) // 2)
                test_proxies = random.sample(list(self.proxies.items()), sample_size)
                
                for proxy_url, metrics in test_proxies:
                    # Simple connectivity test
                    success = await self._test_proxy_connectivity(proxy_url)
                    
                    if not success:
                        metrics.consecutive_failures += 1
                        metrics.last_failure = datetime.now()
                        self._update_health_score(metrics)
                        
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def _test_proxy_connectivity(self, proxy_url: str) -> bool:
        """Test proxy connectivity"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy_url
                ) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def _train_ml_model_loop(self) -> None:
        """Background task to train ML model"""
        while True:
            try:
                await asyncio.sleep(3600)  # Train every hour
                
                if len(self.feature_history) > 100:
                    await self._train_ml_model()
                    
            except Exception as e:
                logger.error(f"ML training error: {e}")
                
    async def _train_ml_model(self) -> None:
        """Train ML model on historical data"""
        try:
            # Prepare training data
            X = np.array([features for features, _ in self.feature_history])
            y = np.array([success for _, success in self.feature_history])
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X, y)
            
            self.ml_model = model
            
            # Save model
            model_path = "proxy_ml_model.pkl"
            joblib.dump(model, model_path)
            
            logger.info(f"Trained ML model on {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get proxy rotation statistics"""
        total_proxies = len(self.proxies)
        healthy_proxies = sum(1 for m in self.proxies.values() if self._is_proxy_healthy(m))
        
        total_requests = sum(m.total_requests for m in self.proxies.values())
        total_success = sum(m.successful_requests for m in self.proxies.values())
        total_detected = sum(m.detected_requests for m in self.proxies.values())
        total_cost = sum(m.total_cost for m in self.proxies.values())
        
        platform_stats = defaultdict(lambda: {'requests': 0, 'success': 0, 'detected': 0})
        
        for record in self.request_history[-1000:]:  # Last 1000 requests
            platform = record['platform']
            platform_stats[platform]['requests'] += 1
            if record['success']:
                platform_stats[platform]['success'] += 1
            if record['detected']:
                platform_stats[platform]['detected'] += 1
                
        return {
            'total_proxies': total_proxies,
            'healthy_proxies': healthy_proxies,
            'active_sessions': len(self.active_proxies),
            'total_requests': total_requests,
            'success_rate': total_success / max(1, total_requests),
            'detection_rate': total_detected / max(1, total_requests),
            'total_cost': total_cost,
            'ml_model_trained': self.ml_model is not None,
            'training_samples': len(self.feature_history),
            'platform_stats': dict(platform_stats),
            'top_proxies': self._get_top_proxies(5)
        }
        
    def _get_top_proxies(self, n: int) -> List[Dict[str, Any]]:
        """Get top performing proxies"""
        proxy_list = []
        
        for proxy_url, metrics in self.proxies.items():
            if metrics.total_requests > 0:
                proxy_list.append({
                    'proxy': proxy_url,
                    'provider': metrics.provider,
                    'location': metrics.location,
                    'health_score': metrics.health_score,
                    'success_rate': metrics.successful_requests / metrics.total_requests,
                    'avg_response_time': metrics.avg_response_time,
                    'total_requests': metrics.total_requests
                })
                
        # Sort by health score
        proxy_list.sort(key=lambda x: x['health_score'], reverse=True)
        
        return proxy_list[:n]
        
    def export_metrics(self, filepath: str) -> None:
        """Export detailed metrics for analysis"""
        metrics_data = {
            'proxies': {},
            'request_history': self.request_history[-1000:],
            'statistics': self.get_statistics()
        }
        
        for proxy_url, metrics in self.proxies.items():
            metrics_data['proxies'][proxy_url] = {
                'provider': metrics.provider,
                'location': metrics.location,
                'type': metrics.proxy_type,
                'health_score': metrics.health_score,
                'total_requests': metrics.total_requests,
                'success_rate': metrics.successful_requests / max(1, metrics.total_requests),
                'detection_rate': metrics.detected_requests / max(1, metrics.total_requests),
                'avg_response_time': metrics.avg_response_time,
                'platform_success': metrics.platform_success,
                'platform_detection': metrics.platform_detection
            }
            
        import json
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)