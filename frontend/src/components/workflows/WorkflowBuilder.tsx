import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  ConnectionMode,
  Panel,
  NodeTypes,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@mui/material';
import { useSupabase } from '../../hooks/useSupabase';
import { useAuth } from '../../hooks/useAuth';

// Import custom node types
import SourceNode from './NodeTypes/SourceNode';
import DestinationNode from './NodeTypes/DestinationNode';
import ConditionNode from './NodeTypes/ConditionNode';
import ActionNode from './NodeTypes/ActionNode';
import ScheduleNode from './NodeTypes/ScheduleNode';
import SplitNode from './NodeTypes/SplitNode';
import MergeNode from './NodeTypes/MergeNode';

// Node type components
const nodeTypes: NodeTypes = {
  source: SourceNode,
  destination: DestinationNode,
  condition: ConditionNode,
  action: ActionNode,
  schedule: ScheduleNode,
  split: SplitNode,
  merge: MergeNode,
};

// Initial nodes for new workflow
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'source',
    position: { x: 250, y: 50 },
    data: { 
      label: 'Income Source',
      accountId: null,
      amount: null,
    },
  },
];

const initialEdges: Edge[] = [];

interface WorkflowBuilderProps {
  workflowId?: string;
  onSave: (workflow: any) => void;
}

export default function WorkflowBuilder({ workflowId, onSave }: WorkflowBuilderProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const { supabase } = useSupabase();
  const { user } = useAuth();

  // Load existing workflow if ID provided
  React.useEffect(() => {
    if (workflowId) {
      loadWorkflow();
    }
  }, [workflowId]);

  const loadWorkflow = async () => {
    const { data, error } = await supabase
      .from('workflows')
      .select('*')
      .eq('id', workflowId)
      .single();

    if (data && data.configuration) {
      setNodes(data.configuration.nodes || []);
      setEdges(data.configuration.edges || []);
    }
  };

  const onConnect = useCallback(
    (params: Connection) => {
      const edge = {
        ...params,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        style: {
          strokeWidth: 2,
          stroke: '#1976d2',
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const addNode = useCallback((type: string) => {
    const newNode: Node = {
      id: `${Date.now()}`,
      type,
      position: { x: 250, y: nodes.length * 100 + 100 },
      data: getDefaultNodeData(type),
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes, setNodes]);

  const getDefaultNodeData = (type: string) => {
    switch (type) {
      case 'source':
        return { label: 'Income Source', accountId: null, amount: null };
      case 'destination':
        return { label: 'Expense/Savings', accountId: null, category: null };
      case 'condition':
        return { label: 'If/Then', condition: null, trueOutput: null, falseOutput: null };
      case 'action':
        return { label: 'Action', actionType: 'transfer', parameters: {} };
      case 'schedule':
        return { label: 'Schedule', cronExpression: null, timezone: 'UTC' };
      case 'split':
        return { label: 'Split Amount', splits: [] };
      case 'merge':
        return { label: 'Merge Flows', sources: [] };
      default:
        return { label: type };
    }
  };

  const saveWorkflow = async () => {
    const workflowData = {
      name: 'My Workflow', // This would come from a form
      description: 'Workflow description',
      status: 'draft',
      configuration: {
        nodes,
        edges,
      },
      user_id: user?.id,
    };

    if (workflowId) {
      // Update existing workflow
      const { error } = await supabase
        .from('workflows')
        .update(workflowData)
        .eq('id', workflowId);

      if (!error) {
        onSave(workflowData);
      }
    } else {
      // Create new workflow
      const { data, error } = await supabase
        .from('workflows')
        .insert(workflowData)
        .select()
        .single();

      if (data) {
        onSave(data);
      }
    }
  };

  const validateWorkflow = useCallback(() => {
    // Check if all nodes are connected
    const nodeIds = nodes.map(n => n.id);
    const connectedNodeIds = new Set<string>();
    
    edges.forEach(edge => {
      connectedNodeIds.add(edge.source);
      connectedNodeIds.add(edge.target);
    });

    const unconnectedNodes = nodeIds.filter(id => !connectedNodeIds.has(id));
    
    if (unconnectedNodes.length > 0 && nodes.length > 1) {
      return { valid: false, message: 'All nodes must be connected' };
    }

    // Check for cycles
    // TODO: Implement cycle detection

    return { valid: true, message: 'Workflow is valid' };
  }, [nodes, edges]);

  const nodeColorMap = {
    source: '#4caf50',
    destination: '#ff9800',
    condition: '#2196f3',
    action: '#9c27b0',
    schedule: '#00bcd4',
    split: '#ffeb3b',
    merge: '#795548',
  };

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
      >
        <Background variant="dots" gap={12} size={1} />
        <Controls />
        
        <Panel position="top-left">
          <div style={{ padding: '10px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3>Add Nodes</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addNode('source')}
                style={{ borderColor: nodeColorMap.source, color: nodeColorMap.source }}
              >
                + Income Source
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addNode('destination')}
                style={{ borderColor: nodeColorMap.destination, color: nodeColorMap.destination }}
              >
                + Destination
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addNode('condition')}
                style={{ borderColor: nodeColorMap.condition, color: nodeColorMap.condition }}
              >
                + Condition
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addNode('action')}
                style={{ borderColor: nodeColorMap.action, color: nodeColorMap.action }}
              >
                + Action
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addNode('split')}
                style={{ borderColor: nodeColorMap.split, color: nodeColorMap.split }}
              >
                + Split
              </Button>
            </div>
          </div>
        </Panel>

        <Panel position="top-right">
          <div style={{ padding: '10px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <Button 
              variant="contained" 
              onClick={saveWorkflow}
              disabled={!validateWorkflow().valid}
            >
              Save Workflow
            </Button>
            {!validateWorkflow().valid && (
              <p style={{ color: 'red', fontSize: '12px', marginTop: '8px' }}>
                {validateWorkflow().message}
              </p>
            )}
          </div>
        </Panel>
      </ReactFlow>

      {/* Node configuration panel would go here */}
      {selectedNode && (
        <div style={{ 
          position: 'absolute', 
          right: 0, 
          top: 0, 
          width: '300px', 
          height: '100%', 
          background: 'white',
          boxShadow: '-2px 0 4px rgba(0,0,0,0.1)',
          padding: '20px',
          overflowY: 'auto'
        }}>
          <h3>Configure Node</h3>
          <p>Type: {selectedNode.type}</p>
          <p>ID: {selectedNode.id}</p>
          {/* Add node-specific configuration forms here */}
        </div>
      )}
    </div>
  );
}