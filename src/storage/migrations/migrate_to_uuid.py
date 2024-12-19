import os
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sqlite3
from datetime import datetime

def migrate_to_uuid():
    """Migrate the database to use UUIDs for agent IDs"""
    
    # Create engine
    database_url = os.getenv('DATABASE_URL', "sqlite:///godfarda.db")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Clean up any previous migration attempts
        try:
            session.execute(text("DROP TABLE IF EXISTS temp_agents"))
            session.execute(text("DROP TABLE IF EXISTS temp_tools"))
            session.execute(text("DROP TABLE IF EXISTS temp_agent_executions"))
        except Exception as e:
            print(f"Warning during cleanup: {str(e)}")
        
        # Create new tables with UUID columns
        session.execute(text("""
            CREATE TABLE temp_agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                system_prompt TEXT,
                agent_type TEXT,
                agent_status TEXT DEFAULT 'Active',
                version TEXT DEFAULT '1.0',
                agent_role TEXT,
                execution_frequency TEXT DEFAULT 'On-Demand',
                response_time TEXT,
                last_executed_by TEXT,
                error_count INTEGER DEFAULT 0,
                config_data TEXT,
                is_active BOOLEAN DEFAULT 1,
                max_chain_depth INTEGER DEFAULT 3,
                chain_strategy TEXT DEFAULT 'sequential',
                temperature REAL DEFAULT 0.7,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        
        session.execute(text("""
            CREATE TABLE temp_tools (
                id INTEGER PRIMARY KEY,
                agent_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                config_data TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES temp_agents(id)
            )
        """))
        
        session.execute(text("""
            CREATE TABLE temp_agent_executions (
                id INTEGER PRIMARY KEY,
                agent_id TEXT,
                conversation_id INTEGER,
                input_data TEXT,
                output_data TEXT,
                execution_data TEXT,
                status TEXT,
                error_message TEXT,
                is_vectorized BOOLEAN DEFAULT 0,
                vectorized_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES temp_agents(id)
            )
        """))
        
        # Copy data from old tables to new ones
        agents = session.execute(text("SELECT * FROM agents")).fetchall()
        current_time = datetime.utcnow().isoformat()
        
        for agent in agents:
            new_id = str(uuid.uuid4())
            # Convert agent.config_data to string if it's not None
            config_data = str(agent.config_data) if agent.config_data else None
            
            # Convert datetime objects to ISO format strings
            created_at = current_time
            updated_at = current_time
            
            if hasattr(agent, 'created_at') and agent.created_at:
                if isinstance(agent.created_at, datetime):
                    created_at = agent.created_at.isoformat()
                elif isinstance(agent.created_at, str):
                    created_at = agent.created_at
            
            if hasattr(agent, 'updated_at') and agent.updated_at:
                if isinstance(agent.updated_at, datetime):
                    updated_at = agent.updated_at.isoformat()
                elif isinstance(agent.updated_at, str):
                    updated_at = agent.updated_at
            
            session.execute(
                text("""
                    INSERT INTO temp_agents (
                        id, name, description, system_prompt, agent_type,
                        agent_status, version, agent_role, execution_frequency,
                        response_time, last_executed_by, error_count,
                        config_data, is_active, max_chain_depth,
                        chain_strategy, temperature, created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :system_prompt, :agent_type,
                        :agent_status, :version, :agent_role, :execution_frequency,
                        :response_time, :last_executed_by, :error_count,
                        :config_data, :is_active, :max_chain_depth,
                        :chain_strategy, :temperature, :created_at, :updated_at
                    )
                """),
                {
                    "id": new_id,
                    "name": agent.name,
                    "description": agent.description,
                    "system_prompt": agent.system_prompt,
                    "agent_type": agent.agent_type if hasattr(agent, 'agent_type') else None,
                    "agent_status": agent.agent_status if hasattr(agent, 'agent_status') else 'Active',
                    "version": agent.version if hasattr(agent, 'version') else '1.0',
                    "agent_role": agent.agent_role if hasattr(agent, 'agent_role') else None,
                    "execution_frequency": agent.execution_frequency if hasattr(agent, 'execution_frequency') else 'On-Demand',
                    "response_time": agent.response_time if hasattr(agent, 'response_time') else None,
                    "last_executed_by": agent.last_executed_by if hasattr(agent, 'last_executed_by') else None,
                    "error_count": agent.error_count if hasattr(agent, 'error_count') else 0,
                    "config_data": config_data,
                    "is_active": agent.is_active if hasattr(agent, 'is_active') else True,
                    "max_chain_depth": agent.max_chain_depth if hasattr(agent, 'max_chain_depth') else 3,
                    "chain_strategy": agent.chain_strategy if hasattr(agent, 'chain_strategy') else 'sequential',
                    "temperature": agent.temperature if hasattr(agent, 'temperature') else 0.7,
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            )
            
            # Update tools and executions with the new UUID
            tools = session.execute(
                text("SELECT * FROM tools WHERE agent_id = :old_id"),
                {"old_id": agent.id}
            ).fetchall()
            
            for tool in tools:
                tool_created_at = current_time
                tool_updated_at = current_time
                
                if hasattr(tool, 'created_at') and tool.created_at:
                    if isinstance(tool.created_at, datetime):
                        tool_created_at = tool.created_at.isoformat()
                    elif isinstance(tool.created_at, str):
                        tool_created_at = tool.created_at
                
                if hasattr(tool, 'updated_at') and tool.updated_at:
                    if isinstance(tool.updated_at, datetime):
                        tool_updated_at = tool.updated_at.isoformat()
                    elif isinstance(tool.updated_at, str):
                        tool_updated_at = tool.updated_at
                
                session.execute(
                    text("""
                        INSERT INTO temp_tools (
                            id, agent_id, name, description, config_data,
                            is_active, created_at, updated_at
                        ) VALUES (
                            :id, :agent_id, :name, :description, :config_data,
                            :is_active, :created_at, :updated_at
                        )
                    """),
                    {
                        "id": tool.id,
                        "agent_id": new_id,
                        "name": tool.name,
                        "description": tool.description,
                        "config_data": str(tool.config_data) if tool.config_data else None,
                        "is_active": tool.is_active if hasattr(tool, 'is_active') else True,
                        "created_at": tool_created_at,
                        "updated_at": tool_updated_at
                    }
                )
            
            executions = session.execute(
                text("SELECT * FROM agent_executions WHERE agent_id = :old_id"),
                {"old_id": agent.id}
            ).fetchall()
            
            for execution in executions:
                exec_created_at = current_time
                exec_updated_at = current_time
                exec_vectorized_at = None
                
                if hasattr(execution, 'created_at') and execution.created_at:
                    if isinstance(execution.created_at, datetime):
                        exec_created_at = execution.created_at.isoformat()
                    elif isinstance(execution.created_at, str):
                        exec_created_at = execution.created_at
                
                if hasattr(execution, 'updated_at') and execution.updated_at:
                    if isinstance(execution.updated_at, datetime):
                        exec_updated_at = execution.updated_at.isoformat()
                    elif isinstance(execution.updated_at, str):
                        exec_updated_at = execution.updated_at
                
                if hasattr(execution, 'vectorized_at') and execution.vectorized_at:
                    if isinstance(execution.vectorized_at, datetime):
                        exec_vectorized_at = execution.vectorized_at.isoformat()
                    elif isinstance(execution.vectorized_at, str):
                        exec_vectorized_at = execution.vectorized_at
                
                session.execute(
                    text("""
                        INSERT INTO temp_agent_executions (
                            id, agent_id, conversation_id, input_data,
                            output_data, execution_data, status,
                            error_message, is_vectorized, vectorized_at,
                            created_at, updated_at
                        ) VALUES (
                            :id, :agent_id, :conversation_id, :input_data,
                            :output_data, :execution_data, :status,
                            :error_message, :is_vectorized, :vectorized_at,
                            :created_at, :updated_at
                        )
                    """),
                    {
                        "id": execution.id,
                        "agent_id": new_id,
                        "conversation_id": execution.conversation_id,
                        "input_data": str(execution.input_data) if execution.input_data else None,
                        "output_data": str(execution.output_data) if execution.output_data else None,
                        "execution_data": str(execution.execution_data) if execution.execution_data else None,
                        "status": execution.status,
                        "error_message": execution.error_message,
                        "is_vectorized": execution.is_vectorized if hasattr(execution, 'is_vectorized') else False,
                        "vectorized_at": exec_vectorized_at,
                        "created_at": exec_created_at,
                        "updated_at": exec_updated_at
                    }
                )
        
        # Replace old tables with new ones
        session.execute(text("DROP TABLE IF EXISTS agents"))
        session.execute(text("DROP TABLE IF EXISTS tools"))
        session.execute(text("DROP TABLE IF EXISTS agent_executions"))
        
        session.execute(text("ALTER TABLE temp_agents RENAME TO agents"))
        session.execute(text("ALTER TABLE temp_tools RENAME TO tools"))
        session.execute(text("ALTER TABLE temp_agent_executions RENAME TO agent_executions"))
        
        # Create indexes
        session.execute(text("CREATE INDEX ix_tools_agent_id ON tools(agent_id)"))
        session.execute(text("CREATE INDEX ix_agent_executions_agent_id ON agent_executions(agent_id)"))
        
        session.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_to_uuid()
