"""
🔥 Sistem de Indexare Semantică
================================
Indexare vectorială și căutare semantică (RAG) peste tot conținutul procesat
Folosește SQLite + embeddings locale (sentence-transformers)
"""

import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class SemanticIndexer:
    """
    Indexare semantică folosind embeddings + SQLite
    Simplificat pentru a evita dependențe heavy (pgvector/Qdrant)
    """
    
    def __init__(self, db_path: str = 'storage/semantic_index.db'):
        """
        Inițializare indexer
        
        Args:
            db_path: Cale către baza de date SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inițializare model de embeddings (lazy loading)
        self.model = None
        self.embedding_dim = 384  # all-MiniLM-L6-v2
        
        # Creare tabel dacă nu există
        self._init_database()
    
    def _init_database(self):
        """Creează tabelele necesare în SQLite"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabel principal pentru documente
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE NOT NULL,
            source_type TEXT,
            filename TEXT,
            lang TEXT,
            domain TEXT,
            topic TEXT,
            info_level TEXT,
            total_segments INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabel pentru segmente (chunks) cu embeddings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            segment_index INTEGER,
            text TEXT NOT NULL,
            embedding_json TEXT,
            page_number INTEGER,
            slide_number INTEGER,
            timestamp_start REAL,
            timestamp_end REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (document_id)
        )
        ''')
        
        # Index pentru căutare rapidă
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_id ON segments(document_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_source_type ON documents(source_type)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_domain ON documents(domain)
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"[INDEXER] ✅ Database initialized: {self.db_path}")
    
    def _load_model(self):
        """Lazy loading pentru modelul de embeddings"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("[INDEXER] Loading embedding model...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[INDEXER] ✅ Model loaded")
            except ImportError:
                print("[INDEXER] ⚠️ sentence-transformers not installed, using fallback")
                self.model = None
    
    def _compute_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Calculează embedding pentru un text
        
        Args:
            text: Text de procesat
            
        Returns:
            Numpy array cu embedding sau None
        """
        self._load_model()
        
        if self.model is None:
            # Fallback: simple word count vector (nu ideal, dar funcționează)
            words = text.lower().split()[:100]
            # Hash simplu pentru a crea un pseudo-embedding
            vec = np.zeros(self.embedding_dim)
            for i, word in enumerate(words):
                idx = hash(word) % self.embedding_dim
                vec[idx] += 1.0
            # Normalizare
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"[INDEXER] Error computing embedding: {e}")
            return None
    
    def index_document(
        self, 
        document_id: str,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Indexează un document complet cu toate segmentele
        
        Args:
            document_id: ID unic al documentului
            segments: Listă de segmente (chunks) de text
                     Fiecare segment: {'text': str, 'page': int, 'slide': int, 'timestamp': tuple}
            metadata: Metadate (source_type, filename, lang, domain, topic, info_level)
            
        Returns:
            Dict cu statistici de indexare
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Inserare/update document
            cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (document_id, source_type, filename, lang, domain, topic, info_level, total_segments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                metadata.get('source_type', 'unknown'),
                metadata.get('filename', 'unknown'),
                metadata.get('lang', 'ro'),
                metadata.get('domain', 'general'),
                metadata.get('topic', ''),
                metadata.get('info_level', 'detailed'),
                len(segments)
            ))
            
            # Șterge segmentele vechi (dacă e re-indexare)
            cursor.execute('DELETE FROM segments WHERE document_id = ?', (document_id,))
            
            # Indexare segmente
            indexed_count = 0
            for i, segment in enumerate(segments):
                text = segment.get('text', '').strip()
                if not text or len(text) < 10:
                    continue
                
                # Calculează embedding
                embedding = self._compute_embedding(text)
                embedding_json = json.dumps(embedding.tolist()) if embedding is not None else None
                
                cursor.execute('''
                INSERT INTO segments 
                (document_id, segment_index, text, embedding_json, 
                 page_number, slide_number, timestamp_start, timestamp_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    i,
                    text,
                    embedding_json,
                    segment.get('page'),
                    segment.get('slide'),
                    segment.get('timestamp', (None, None))[0] if isinstance(segment.get('timestamp'), tuple) else None,
                    segment.get('timestamp', (None, None))[1] if isinstance(segment.get('timestamp'), tuple) else None
                ))
                
                indexed_count += 1
                
                # Progress feedback
                if (i + 1) % 50 == 0:
                    print(f"[INDEXER] Indexed {i + 1}/{len(segments)} segments")
            
            conn.commit()
            conn.close()
            
            print(f"[INDEXER] ✅ Indexed document: {document_id} ({indexed_count} segments)")
            
            return {
                'success': True,
                'document_id': document_id,
                'indexed_segments': indexed_count,
                'total_segments': len(segments)
            }
            
        except Exception as e:
            print(f"[INDEXER] ERROR indexing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_semantic(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Căutare semantică în index
        
        Args:
            query: Întrebarea/textul de căutat
            filters: Filtre opționale (source_type, domain, lang)
            top_k: Număr maxim de rezultate
            
        Returns:
            Listă de rezultate sortate după relevanță
        """
        try:
            # Calculează embedding pentru query
            query_embedding = self._compute_embedding(query)
            if query_embedding is None:
                return []
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Construiește query SQL cu filtre
            sql = '''
            SELECT 
                s.id, s.document_id, s.text, s.embedding_json,
                s.page_number, s.slide_number, s.timestamp_start, s.timestamp_end,
                d.source_type, d.filename, d.domain, d.topic, d.lang
            FROM segments s
            JOIN documents d ON s.document_id = d.document_id
            WHERE s.embedding_json IS NOT NULL
            '''
            
            params = []
            
            if filters:
                if 'source_type' in filters and filters['source_type']:
                    sql += ' AND d.source_type IN ({})'.format(
                        ','.join(['?' for _ in filters['source_type']])
                    )
                    params.extend(filters['source_type'])
                
                if 'domain' in filters and filters['domain']:
                    sql += ' AND d.domain IN ({})'.format(
                        ','.join(['?' for _ in filters['domain']])
                    )
                    params.extend(filters['domain'])
                
                if 'lang' in filters and filters['lang']:
                    sql += ' AND d.lang IN ({})'.format(
                        ','.join(['?' for _ in filters['lang']])
                    )
                    params.extend(filters['lang'])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Calculează similaritate cosinus pentru fiecare rezultat
            results = []
            for row in rows:
                seg_embedding_json = row[3]
                if not seg_embedding_json:
                    continue
                
                seg_embedding = np.array(json.loads(seg_embedding_json))
                
                # Similaritate cosinus
                similarity = np.dot(query_embedding, seg_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(seg_embedding) + 1e-8
                )
                
                results.append({
                    'segment_id': row[0],
                    'document_id': row[1],
                    'text_snippet': row[2][:500],  # primele 500 caractere
                    'full_text': row[2],
                    'page': row[4],
                    'slide': row[5],
                    'timestamp_start': row[6],
                    'timestamp_end': row[7],
                    'source_type': row[8],
                    'filename': row[9],
                    'domain': row[10],
                    'topic': row[11],
                    'lang': row[12],
                    'score': float(similarity)
                })
            
            # Sortează după scor și returnează top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"[INDEXER] ERROR in search: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Returnează statistici despre indexul semantic"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM documents')
            total_docs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM segments')
            total_segments = cursor.fetchone()[0]
            
            cursor.execute('SELECT source_type, COUNT(*) FROM documents GROUP BY source_type')
            by_type = dict(cursor.fetchall())
            
            cursor.execute('SELECT domain, COUNT(*) FROM documents GROUP BY domain')
            by_domain = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_documents': total_docs,
                'total_segments': total_segments,
                'by_source_type': by_type,
                'by_domain': by_domain
            }
        except Exception as e:
            print(f"[INDEXER] ERROR getting stats: {e}")
            return {}
    
    def delete_document(self, document_id: str) -> bool:
        """Șterge un document și toate segmentele asociate"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM segments WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM documents WHERE document_id = ?', (document_id,))
            
            conn.commit()
            conn.close()
            
            print(f"[INDEXER] ✅ Deleted document: {document_id}")
            return True
        except Exception as e:
            print(f"[INDEXER] ERROR deleting document: {e}")
            return False


# Test standalone
if __name__ == "__main__":
    indexer = SemanticIndexer()
    
    # Test indexare
    test_segments = [
        {
            'text': 'Telomeraza este o enzimă importantă pentru replicarea ADN-ului.',
            'page': 1,
            'slide': None,
            'timestamp': None
        },
        {
            'text': 'Studiile asupra telomerazei au implicații în cercetarea cancerului.',
            'page': 2,
            'slide': None,
            'timestamp': None
        }
    ]
    
    result = indexer.index_document(
        document_id='test_doc_001',
        segments=test_segments,
        metadata={
            'source_type': 'document',
            'filename': 'biology_research.pdf',
            'lang': 'ro',
            'domain': 'scientific',
            'topic': 'Telomeraza și cercetarea cancerului',
            'info_level': 'technical'
        }
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test căutare
    results = indexer.search_semantic(
        query='Găsește informații despre telomerază',
        top_k=5
    )
    print(f"\n📊 Found {len(results)} results:")
    for r in results:
        print(f"  Score: {r['score']:.3f} - {r['text_snippet'][:100]}...")
    
    # Statistici
    stats = indexer.get_document_stats()
    print(f"\n📈 Index stats:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
