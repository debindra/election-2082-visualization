"""
Embedding Service using Sentence Transformers

Generates embeddings for candidate and voting center data.
With Redis caching for improved performance.
"""
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from config.settings import settings
from services.redis_cache import RedisCacheService

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.
    
    Supports multilingual text (Nepali and English).
    Includes Redis caching for repeated text embeddings.
    """
    
    def __init__(self, 
                 model_name: str = None,
                 device: str = None):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of sentence transformer model
            device: Device to run model on ('cpu' or 'cuda')
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        
        logger.info(f"Loading embedding model: {self.model_name}")
        logger.info(f"Device: {self.device}")
        
        # Load model
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize Redis cache
        self.cache = RedisCacheService()
        if self.cache.enabled:
            logger.info("Embedding cache enabled")
        
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        logger.info("Embedding service initialized successfully")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if not texts:
            return np.array([]).reshape(0, self.embedding_dim)
        
        # Try to get cached embeddings
        if self.cache.enabled:
            embeddings = []
            uncached_indices = []
            uncached_texts = []
            
            for i, text in enumerate(texts):
                cached = self.cache.get_cached_embedding(text)
                if cached is not None:
                    embeddings.append(cached)
                else:
                    embeddings.append(None)
                    uncached_indices.append(i)
                    uncached_texts.append(text)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                try:
                    new_embeddings = self._generate_embeddings(uncached_texts)
                    
                    # Cache new embeddings
                    for text, emb in zip(uncached_texts, new_embeddings):
                        self.cache.cache_embedding(text, emb)
                    
                    # Replace None values with new embeddings
                    for idx, emb in zip(uncached_indices, new_embeddings):
                        embeddings[idx] = emb
                    
                except Exception as e:
                    logger.error(f"Error generating embeddings: {e}")
                    raise
            
            # Convert list to array
            return np.array(embeddings)
        
        # No caching - generate all embeddings
        return self._generate_embeddings(texts)
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings without caching (internal method).
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for better similarity
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Numpy array of embedding (shape: [embedding_dim])
        """
        # Check cache first
        if self.cache.enabled:
            cached = self.cache.get_cached_embedding(text)
            if cached is not None:
                logger.debug("Embedding cache hit for single text")
                return cached
        
        # Generate new embedding
        embedding = self.embed([text])[0]
        
        # Cache it
        if self.cache.enabled:
            self.cache.cache_embedding(text, embedding)
        
        return embedding
    
    def create_candidate_text(self, candidate_row: dict) -> str:
        """
        Create rich text representation for candidate.
        
        Includes all relevant fields for better semantic matching.
        """
        name_np = candidate_row.get('Candidate Full Name', '')
        name_en = candidate_row.get('Candidate Full Name in English', '')
        party_np = candidate_row.get('Political Party', '')
        party_en = candidate_row.get('Political Party In English', '')
        symbol = candidate_row.get('Election Symbol', '')
        area = candidate_row.get('Election Area', '')
        district = candidate_row.get('District', '')
        district_en = candidate_row.get('District in English', '')
        state = candidate_row.get('State', '')
        state_en = candidate_row.get('State in English', '')
        gender = candidate_row.get('Gender', '')
        education = candidate_row.get('Academic qualification', '')
        university = candidate_row.get('University', '')
        experience = candidate_row.get('Experience', '')
        dob = candidate_row.get('DOB', '')
        birth_place = candidate_row.get('Birth Place', '')
        birth_place_en = candidate_row.get('Birth Place In english', '')
        spouse = candidate_row.get('Spouse Name', '')
        
        text = f"""
Candidate: {name_np} ({name_en})
Party: {party_np} ({party_en})
Symbol: {symbol}
Constituency: {area} in {district} ({district_en})
State: {state} ({state_en})
Gender: {gender}
Education: {education} from {university}
Experience: {experience}
Date of Birth: {dob}
Birth Place: {birth_place} ({birth_place_en})
Spouse: {spouse if spouse else 'N/A'}
""".strip()
        
        return text
    
    def create_voting_center_text(self, vc_row: dict) -> str:
        """
        Create rich text representation for voting center.
        """
        center_name = vc_row.get('polling_center_name', '')
        center_code = vc_row.get('polling_center_code', '')
        district = vc_row.get('district', '')
        district_en = vc_row.get('district_name_english', '')
        province = vc_row.get('province', '')
        area_no = vc_row.get('area_no', '')
        palika_type = vc_row.get('palika_type', '')
        palika_name = vc_row.get('palika_name', '')
        palika_name_en = vc_row.get('palika_name_en', '')
        ward_no = vc_row.get('ward_no', '')
        sub_center = vc_row.get('sub_center', '')
        voter_count = vc_row.get('voter_count', '')
        language = vc_row.get('language', '')
        
        text = f"""
Voting Center: {center_name} (Code: {center_code})
Location: {district} ({district_en}), {province}
Area Number: {area_no}
Palika: {palika_type} {palika_name} ({palika_name_en})
Ward: {ward_no}
Sub Center: {sub_center if sub_center else 'N/A'}
Total Voters: {voter_count}
Language: {language}
""".strip()
        
        return text
    
    def batch_embed_candidates(self, candidates_df) -> tuple:
        """
        Generate embeddings for all candidates in a dataframe.
        
        Args:
            candidates_df: Pandas DataFrame of candidates
            
        Returns:
            Tuple of (embeddings, texts, metadata)
        """
        logger.info(f"Generating embeddings for {len(candidates_df)} candidates")
        
        texts = []
        metadata_list = []
        
        for _, row in candidates_df.iterrows():
            text = self.create_candidate_text(row.to_dict())
            texts.append(text)
            
            # Create metadata
            metadata = {
                "source_type": "candidate",
                "content": text,
                "candidate_id": str(row.get('Index', '')),
                "name_np": row.get('Candidate Full Name', ''),
                "name_en": row.get('Candidate Full Name in English', ''),
                "party_np": row.get('Political Party', ''),
                "party_en": row.get('Political Party In English', ''),
                "symbol": row.get('Election Symbol', ''),
                "gender": row.get('Gender', ''),
                "education": row.get('Academic qualification', ''),
                "university": row.get('University', ''),
                "district": row.get('District', ''),
                "district_en": row.get('District in English', ''),
                "state": row.get('State', ''),
                "state_en": row.get('State in English', ''),
                "area_no": row.get('area_no', ''),
                "constituency": row.get('Election Area', ''),
                "dob": row.get('DOB', ''),
                "birth_place": row.get('Birth Place', ''),
                "birth_place_en": row.get('Birth Place In english', ''),
                "spouse_name": row.get('Spouse Name', ''),
                "spouse_name_en": row.get('Spouse Name in English', ''),
                "experience": row.get('Experience', ''),
                "image_url": row.get('Image URL', ''),
            }
            metadata_list.append(metadata)
        
        # Generate embeddings (with caching)
        embeddings = self.embed(texts)
        
        logger.info(f"Generated {len(embeddings)} candidate embeddings")
        return embeddings, texts, metadata_list
    
    def batch_embed_voting_centers(self, vc_df) -> tuple:
        """
        Generate embeddings for all voting centers in a dataframe.
        
        Args:
            vc_df: Pandas DataFrame of voting centers
            
        Returns:
            Tuple of (embeddings, texts, metadata)
        """
        logger.info(f"Generating embeddings for {len(vc_df)} voting centers")
        
        texts = []
        metadata_list = []
        
        for _, row in vc_df.iterrows():
            text = self.create_voting_center_text(row.to_dict())
            texts.append(text)
            
            # Create metadata
            metadata = {
                "source_type": "voting_center",
                "content": text,
                "polling_center_code": str(row.get('polling_center_code', '')),
                "polling_center_name": row.get('polling_center_name', ''),
                "district": row.get('district', ''),
                "district_en": row.get('district_name_english', ''),
                "province": row.get('province', ''),
                "area_no": row.get('area_no', ''),
                "palika_type": row.get('palika_type', ''),
                "palika_name": row.get('palika_name', ''),
                "palika_name_en": row.get('palika_name_en', ''),
                "ward_no": row.get('ward_no', ''),
                "sub_center": row.get('sub_center', ''),
                "voter_count": row.get('voter_count', ''),
                "voter_from_serial": row.get('voter_from_serial', ''),
                "voter_to_serial": row.get('voter_to_serial', ''),
                "source_file": row.get('source_file', ''),
                "language": row.get('language', ''),
            }
            metadata_list.append(metadata)
        
        # Generate embeddings (with caching)
        embeddings = self.embed(texts)
        
        logger.info(f"Generated {len(embeddings)} voting center embeddings")
        return embeddings, texts, metadata_list
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats() if self.cache else {"enabled": False}
