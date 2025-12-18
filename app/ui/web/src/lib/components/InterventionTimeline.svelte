<script lang="ts">
  import { CheckCircle, XCircle } from 'lucide-svelte';
  
  let { interventions } = $props();
</script>
<div class="space-y-4">
  {#each interventions as intervention, index}
    <div class="flex gap-4">
      <div class="flex flex-col items-center">
        {#if intervention.intervention_effective}
          <CheckCircle class="text-success" size={24} />
        {:else}
          <XCircle class="text-error" size={24} />
        {/if}
        {#if index < interventions.length - 1}
          <div class="w-0.5 h-full bg-base-300 mt-2"></div>
        {/if}
      </div>
      
      <div class="flex-1 pb-4">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-semibold">{intervention.analysis_date}</span>
          <span class="badge {intervention.intervention_effective ? 'badge-success' : 'badge-error'} badge-sm">
            {intervention.intervention_effective ? 'Effective' : 'Not Effective'}
          </span>
        </div>
        <p class="text-sm text-base-content/70">
          <strong>Issue:</strong> {intervention.reason}
        </p>
        <p class="text-sm text-base-content/70">
          <strong>Action:</strong> {intervention.recommendation}
        </p>
      </div>
    </div>
  {/each}
</div>