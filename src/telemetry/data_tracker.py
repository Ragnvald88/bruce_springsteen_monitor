    
    def _calculate_efficiency(self, metrics: DataUsageMetrics) -> float:
        """Calculate data efficiency score (0-100)"""
        if metrics.requests_made == 0:
            return 100.0
        
        # Base score on data per request
        mb_per_request = metrics.total_mb / metrics.requests_made
        
        # Ideal is < 0.5 MB per request
        if mb_per_request < 0.5:
            base_score = 100
        elif mb_per_request < 1.0:
            base_score = 80
        elif mb_per_request < 2.0:
            base_score = 60
        else:
            base_score = 40
        
        # Bonus for blocking resources
        block_bonus = min(20, (metrics.images_blocked + metrics.scripts_blocked) * 0.1)
        
        return min(100, base_score + block_bonus)
    
    def _generate_recommendations(self, total_mb: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if total_mb > 1000:
            recommendations.append("Enable aggressive image blocking to reduce data usage")
        
        # Platform-specific recommendations
        for platform, metrics in self.platform_totals.items():
            if metrics.requests_made > 0:
                mb_per_request = metrics.total_mb / metrics.requests_made
                if mb_per_request > 2.0:
                    recommendations.append(f"High data usage on {platform} - consider enabling request filtering")
                
                if metrics.images_blocked == 0 and metrics.total_mb > 100:
                    recommendations.append(f"Enable image blocking for {platform} to reduce data usage")
        
        return recommendations
    
    async def generate_report(self) -> str:
        """Generate a detailed usage report"""
        summary = self.get_summary()
        
        report = []
        report.append("=== Data Usage Report ===")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Data Used: {summary['total_data_mb']} MB")
        report.append("")
        
        # Platform breakdown
        report.append("Platform Breakdown:")
        for platform, data in summary['platforms'].items():
            report.append(f"  {platform}:")
            report.append(f"    - Data Used: {data['data_mb']} MB")
            report.append(f"    - Requests: {data['requests']}")
            report.append(f"    - Efficiency: {data['efficiency_score']:.0f}%")
            report.append(f"    - Resources Blocked: {data['images_blocked']} images, {data['scripts_blocked']} scripts")
        
        # Recommendations
        if summary['recommendations']:
            report.append("")
            report.append("Optimization Recommendations:")
            for rec in summary['recommendations']:
                report.append(f"  • {rec}")
        
        return "\n".join(report)
