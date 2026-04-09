'use client';

import { useEffect, useState } from 'react';

interface Approval {
  id: number;
  task_id: number;
  action_name: string;
  requested_action: Record<string, unknown>;
  status: string;
  decision_notes?: string;
  expires_at?: string;
  approved_by?: number;
  approved_at?: string;
}

interface ExecutionResult {
  status: string;
  output?: unknown;
  error?: string;
  [key: string]: unknown;
}

interface Props {
  approval: Approval;
  apiBase: string;
  apiKey: string;
  onClose: () => void;
  onApprove: (approval: Approval, notes: string) => void | Promise<void>;
  onReject: (approvalId: number, notes: string) => void | Promise<void>;
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return dateString;
  }
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'approved':
      return 'bg-green-900 text-green-300 border border-green-700';
    case 'rejected':
      return 'bg-red-900 text-red-300 border border-red-700';
    case 'pending':
    default:
      return 'bg-yellow-900 text-yellow-300 border border-yellow-700';
  }
};

const isExpired = (expiresAt?: string): boolean => {
  if (!expiresAt) return false;
  return new Date(expiresAt) < new Date();
};

export default function ApprovalDetail({
  approval,
  apiBase,
  apiKey,
  onClose,
  onApprove,
  onReject,
}: Props) {
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(
    null
  );
  const [isPolling, setIsPolling] = useState(true);
  const [pollCount, setPollCount] = useState(0);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [pollingStatus, setPollingStatus] = useState<string>('pending');
  const [decisionNotes, setDecisionNotes] = useState('');

  // Real-time status polling
  useEffect(() => {
    if (!isPolling || pollCount >= 30) {
      setIsPolling(false);
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${apiBase}/tasks/${approval.task_id}`, {
          headers: apiKey ? { 'X-API-Key': apiKey } : undefined,
        });
        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();
        setPollingStatus(data.status);

        if (
          data.status === 'completed' ||
          data.status === 'failed' ||
          data.status === 'error'
        ) {
          setExecutionResult(data);
          setIsPolling(false);
        }

        setPollCount((prev) => prev + 1);
      } catch (error) {
        console.error('Polling error:', error);
        setPollCount((prev) => prev + 1);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [isPolling, pollCount, approval.task_id, apiBase]);

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await onApprove(approval, decisionNotes.trim());
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    setIsRejecting(true);
    try {
      await onReject(Number(approval.id), decisionNotes.trim());
    } catch (error) {
      console.error('Rejection error:', error);
    } finally {
      setIsRejecting(false);
    }
  };

  const isPending = approval.status === 'pending';
  const hasExpired = isExpired(approval.expires_at);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 p-4 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Approval Detail
            </h2>
            <p className="text-sm text-zinc-400">Task ID: {approval.task_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-200 text-2xl leading-none"
            aria-label="Close approval detail"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Status Badge */}
          <div className="flex items-center gap-3">
            <span className="text-zinc-400 text-sm">Status:</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                approval.status
              )}`}
            >
              {approval.status.toUpperCase()}
            </span>
            {hasExpired && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-900 text-red-300 border border-red-700">
                EXPIRED
              </span>
            )}
            {isPolling && (
              <span className="px-2 py-1 text-xs text-zinc-400 animate-pulse">
                {pollingStatus}...
              </span>
            )}
          </div>

          {/* Action Name */}
          <div className="bg-zinc-800 rounded-xl p-3">
            <div className="text-zinc-400 text-sm mb-1">Action</div>
            <div className="text-white font-medium">{approval.action_name}</div>
          </div>

          <div className="bg-zinc-800 rounded-xl p-3">
            <label htmlFor="approval-notes" className="text-zinc-400 text-sm mb-2 block">
              Decision Notes (optional)
            </label>
            <textarea
              id="approval-notes"
              value={decisionNotes}
              onChange={(event) => setDecisionNotes(event.target.value)}
              className="w-full min-h-20 rounded-lg bg-zinc-900 border border-zinc-700 p-2 text-sm text-zinc-100 outline-none focus:border-emerald-500"
              placeholder="Add a short reason for your decision"
            />
          </div>

          {/* Expires At */}
          {approval.expires_at && (
            <div className="bg-zinc-800 rounded-xl p-3">
              <div className="text-zinc-400 text-sm mb-1">Expires At</div>
              <div className="text-white">
                {formatDate(approval.expires_at)}
              </div>
            </div>
          )}

          {/* Decision Notes */}
          {approval.decision_notes && (
            <div className="bg-zinc-800 rounded-xl p-3">
              <div className="text-zinc-400 text-sm mb-1">Decision Notes</div>
              <div className="text-white text-sm">{approval.decision_notes}</div>
            </div>
          )}

          {/* Approval Timestamps */}
          {approval.approved_at && (
            <div className="bg-zinc-800 rounded-xl p-3">
              <div className="text-zinc-400 text-sm mb-1">Approved At</div>
              <div className="text-white text-sm">
                {formatDate(approval.approved_at)}
              </div>
            </div>
          )}

          {approval.approved_by && (
            <div className="bg-zinc-800 rounded-xl p-3">
              <div className="text-zinc-400 text-sm mb-1">Approved By</div>
              <div className="text-white text-sm">{approval.approved_by}</div>
            </div>
          )}

          {/* Requested Action (Task Context) */}
          <div className="bg-zinc-800 rounded-xl p-3">
            <div className="text-zinc-400 text-sm mb-2">
              Requested Action
            </div>
            <div className="bg-zinc-900 rounded p-2 text-xs text-zinc-300 font-mono overflow-x-auto">
              <pre>{JSON.stringify(approval.requested_action, null, 2)}</pre>
            </div>
          </div>

          {/* Execution Result */}
          {executionResult && (
            <div className="bg-zinc-800 rounded-xl p-3">
              <div className="text-zinc-400 text-sm mb-2">
                Execution Result
              </div>
              <div
                className={`rounded p-2 text-xs font-mono overflow-x-auto ${
                  executionResult.status === 'completed'
                    ? 'bg-green-900 text-green-300'
                    : 'bg-red-900 text-red-300'
                }`}
              >
                <pre>{JSON.stringify(executionResult, null, 2)}</pre>
              </div>
            </div>
          )}

          {/* Polling Status */}
          {isPolling && pollCount < 30 && (
            <div className="text-xs text-zinc-400 text-center">
              Polling for updates... ({pollCount}/30)
            </div>
          )}
          {pollCount >= 30 && !executionResult && (
            <div className="text-xs text-yellow-600 text-center">
              Polling complete. Task may still be running.
            </div>
          )}
        </div>

        {/* Footer with Actions */}
        <div className="sticky bottom-0 bg-zinc-900 border-t border-zinc-800 p-4 flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-medium transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleReject}
            disabled={!isPending || hasExpired || isRejecting || isApproving}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isPending && !hasExpired && !isRejecting && !isApproving
                ? 'bg-rose-700 hover:bg-rose-600 text-white'
                : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
            }`}
          >
            {isRejecting ? 'Rejecting...' : 'Reject'}
          </button>
          <button
            onClick={handleApprove}
            disabled={!isPending || hasExpired || isApproving || isRejecting}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isPending && !hasExpired && !isApproving && !isRejecting
                ? 'bg-green-700 hover:bg-green-600 text-white'
                : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
            }`}
          >
            {isApproving ? 'Approving...' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  );
}
