<script lang="ts">
  import { AlertTriangle, AlertCircle, Info } from 'lucide-svelte';
  
  let { analysis } = $props();
  
  const alertConfig = {
    high: {
      color: 'alert-error',
      icon: AlertTriangle,
      badge: 'badge-error'
    },
    medium: {
      color: 'alert-warning',
      icon: AlertCircle,
      badge: 'badge-warning'
    },
    low: {
      color: 'alert-info',
      icon: Info,
      badge: 'badge-info'
    }
  };
  
  const config = alertConfig[analysis.alert_level] || alertConfig.low;
  const Icon = config.icon;
</script>
<div class="alert {config.color} shadow-lg">
  <Icon size={24} />
  <div class="flex-1">
    <div class="flex items-center gap-2 mb-1">
      <span class="badge {config.badge} uppercase text-xs font-bold">
        {analysis.alert_level} Alert
      </span>
      <span class="text-xs opacity-70">{analysis.analysis_date}</span>
    </div>
    <h3 class="font-bold">{analysis.reason}</h3>
    <div class="text-sm mt-1">
      <strong>Recommendation:</strong> {analysis.recommendation}
    </div>
  </div>
</div>