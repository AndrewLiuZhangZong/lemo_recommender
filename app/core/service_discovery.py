# -*- coding: utf-8 -*-
"""
Service Discovery for Istio Service Mesh

Features:
1. Istio Service Mesh support (production)
2. K8s Service DNS fallback (development)
3. Simple service name resolution
4. Auto retry and circuit breaker (handled by Envoy Sidecar)

Architecture:
    App -> Envoy Sidecar -> Istio Control Plane -> Target Service Envoy -> Target App

Note:
    In Istio, all traffic policies (load balancing, circuit breaker, retry, timeout)
    are configured in DestinationRule and VirtualService, not in application code.
"""
import os
import grpc
from typing import Optional
from enum import Enum


class ServiceName(str, Enum):
    """Service name constants (like Go's constant package)"""
    
    # Online services
    RECALL = "lemo-service-recommender-recall"
    RANKING = "lemo-service-recommender-ranking"
    RERANKING = "lemo-service-recommender-reranking"
    USER = "lemo-service-recommender-user"
    ITEM = "lemo-service-recommender-item"
    BEHAVIOR = "lemo-service-recommender-behavior"
    
    # Offline services
    MODEL_TRAINING = "lemo-service-recommender-model-training"
    FEATURE_ENGINEERING = "lemo-service-recommender-feature-engineering"
    VECTOR_GENERATION = "lemo-service-recommender-vector-generation"
    
    # Realtime services
    FLINK_REALTIME = "lemo-service-recommender-flink-realtime"
    
    # BFF
    RECOMMENDER = "lemo-service-recommender"


class ServicePort:
    """Service port mapping"""
    
    PORTS = {
        ServiceName.RECALL: 8081,
        ServiceName.RANKING: 8082,
        ServiceName.RERANKING: 8083,
        ServiceName.USER: 8084,
        ServiceName.ITEM: 8085,
        ServiceName.BEHAVIOR: 8086,
        ServiceName.MODEL_TRAINING: 8091,
        ServiceName.FEATURE_ENGINEERING: 8092,
        ServiceName.VECTOR_GENERATION: 8093,
        ServiceName.FLINK_REALTIME: 8094,
        ServiceName.RECOMMENDER: 10072,  # gRPC port
    }
    
    @classmethod
    def get_port(cls, service_name: ServiceName) -> int:
        """Get service port"""
        return cls.PORTS.get(service_name, 8080)


class DiscoveryMode(str, Enum):
    """Service discovery mode"""
    ISTIO = "istio"      # Istio Service Mesh (production)
    K8S = "k8s"          # K8s Service DNS (fallback)
    LOCAL = "local"      # Local development


class ServiceDiscovery:
    """
    Service Discovery for Istio Service Mesh
    
    Usage:
        discovery = ServiceDiscovery()
        channel = discovery.create_channel(ServiceName.RECALL)
        stub = RecallServiceStub(channel)
    
    Environment Variables:
        SERVICE_DISCOVERY_MODE: istio | k8s | local (default: auto-detect)
        K8S_NAMESPACE: kubernetes namespace (default: lemo-dev)
        ISTIO_ENABLED: true | false (default: auto-detect)
    """
    
    def __init__(self):
        self.namespace = os.getenv("K8S_NAMESPACE", "lemo-dev")
        self.mode = self._detect_mode()
        
        print(f"[ServiceDiscovery] Mode: {self.mode}, Namespace: {self.namespace}")
    
    def _detect_mode(self) -> DiscoveryMode:
        """Auto-detect service discovery mode"""
        
        # Manual override
        mode_env = os.getenv("SERVICE_DISCOVERY_MODE", "").lower()
        if mode_env == "istio":
            return DiscoveryMode.ISTIO
        elif mode_env == "k8s":
            return DiscoveryMode.K8S
        elif mode_env == "local":
            return DiscoveryMode.LOCAL
        
        # Auto-detect: check if in K8s
        if not self._is_in_k8s():
            return DiscoveryMode.LOCAL
        
        # Auto-detect: check if Istio is enabled
        istio_enabled = os.getenv("ISTIO_ENABLED", "").lower()
        if istio_enabled == "true":
            return DiscoveryMode.ISTIO
        
        # Check if Envoy sidecar exists (Istio auto-injection)
        if self._has_envoy_sidecar():
            return DiscoveryMode.ISTIO
        
        # Fallback to K8s Service DNS
        return DiscoveryMode.K8S
    
    def _is_in_k8s(self) -> bool:
        """Check if running in Kubernetes"""
        return os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount")
    
    def _has_envoy_sidecar(self) -> bool:
        """Check if Envoy sidecar exists (Istio)"""
        # Envoy admin API is usually at localhost:15000
        return os.path.exists("/etc/istio/proxy") or \
               os.getenv("ISTIO_META_MESH_ID") is not None
    
    def get_service_endpoint(self, service_name: ServiceName) -> str:
        """
        Get service endpoint address
        
        Args:
            service_name: Service name constant
            
        Returns:
            Istio mode: "lemo-service-recall:8081" (Envoy handles discovery)
            K8s mode: "lemo-service-recall.lemo-dev.svc.cluster.local:8081"
            Local mode: "localhost:8081"
        """
        port = ServicePort.get_port(service_name)
        
        if self.mode == DiscoveryMode.ISTIO:
            # Istio: Simple service name, Envoy Sidecar handles everything
            # Envoy will:
            # 1. Resolve service through Istio Pilot
            # 2. Load balance across pods
            # 3. Circuit break on failures
            # 4. Retry on errors
            # 5. Trace with distributed tracing
            return f"{service_name.value}:{port}"
        
        elif self.mode == DiscoveryMode.K8S:
            # K8s Service DNS: Full FQDN
            return f"{service_name.value}.{self.namespace}.svc.cluster.local:{port}"
        
        else:
            # Local development
            return f"localhost:{port}"
    
    def create_channel(
        self,
        service_name: ServiceName,
        timeout: Optional[float] = None
    ) -> grpc.aio.Channel:
        """
        Create gRPC channel
        
        Args:
            service_name: Service name constant
            timeout: Request timeout in seconds (optional)
            
        Returns:
            gRPC async channel
            
        Note:
            In Istio mode, most policies (retry, circuit breaker, timeout) are
            configured in DestinationRule, not here. Application code stays simple.
        """
        endpoint = self.get_service_endpoint(service_name)
        
        # Basic channel options
        options = [
            # Message size limits
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
        
        # Add timeout if specified (Istio VirtualService can override this)
        if timeout:
            options.append(('grpc.timeout', int(timeout * 1000)))
        
        # In Istio mode, keep it simple - Envoy handles:
        # - Service discovery
        # - Load balancing (configured in DestinationRule)
        # - Circuit breaking (configured in DestinationRule)
        # - Retry (configured in VirtualService)
        # - Timeout (configured in VirtualService)
        # - Distributed tracing (automatic)
        # - mTLS encryption (automatic)
        
        if self.mode == DiscoveryMode.ISTIO:
            # Istio: Simple insecure channel, Envoy handles everything
            return grpc.aio.insecure_channel(endpoint, options=options)
        
        elif self.mode == DiscoveryMode.K8S:
            # K8s: Add basic retry and keepalive
            options.extend([
                ('grpc.lb_policy_name', 'round_robin'),
                ('grpc.enable_retries', 1),
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
            ])
            return grpc.aio.insecure_channel(endpoint, options=options)
        
        else:
            # Local: Simple channel
            return grpc.aio.insecure_channel(endpoint, options=options)
    
    def get_http_endpoint(self, service_name: ServiceName, use_https: bool = False) -> str:
        """
        Get HTTP endpoint (for REST APIs)
        
        Args:
            service_name: Service name constant
            use_https: Use HTTPS (Istio mTLS)
            
        Returns:
            HTTP(S) endpoint URL
        """
        port = ServicePort.get_port(service_name)
        protocol = "https" if use_https else "http"
        
        if self.mode == DiscoveryMode.ISTIO:
            return f"{protocol}://{service_name.value}:{port}"
        elif self.mode == DiscoveryMode.K8S:
            return f"{protocol}://{service_name.value}.{self.namespace}.svc.cluster.local:{port}"
        else:
            return f"{protocol}://localhost:{port}"


# Global singleton instance
_discovery: Optional[ServiceDiscovery] = None


def get_service_discovery() -> ServiceDiscovery:
    """Get global service discovery instance (singleton)"""
    global _discovery
    if _discovery is None:
        _discovery = ServiceDiscovery()
    return _discovery


# Convenience functions for common services
def get_recall_channel() -> grpc.aio.Channel:
    """Get recall service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.RECALL)


def get_ranking_channel() -> grpc.aio.Channel:
    """Get ranking service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.RANKING)


def get_reranking_channel() -> grpc.aio.Channel:
    """Get reranking service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.RERANKING)


def get_user_channel() -> grpc.aio.Channel:
    """Get user service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.USER)


def get_item_channel() -> grpc.aio.Channel:
    """Get item service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.ITEM)


def get_behavior_channel() -> grpc.aio.Channel:
    """Get behavior service gRPC channel"""
    return get_service_discovery().create_channel(ServiceName.BEHAVIOR)

