from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.transcript import TranscriptSegment


class ChunkData(BaseModel):
    chunk_index: int
    text: str
    speaker: str
    start_time: float
    end_time: float
    metadata: Dict[str, Any]


class TranscriptChunker:
    """Intelligent transcript chunker with sliding window, speaker aggregation, and timestamp bounds."""

    def __init__(
        self,
        target_word_count: int = 150,
        min_segment_overlap: int = 1,
    ):
        self.target_word_count = target_word_count
        self.min_segment_overlap = min_segment_overlap

    def chunk_segments(self, segments: List[TranscriptSegment]) -> List[ChunkData]:
        """Convert a list of transcript segments into overlapping, timestamped chunks."""
        if not segments:
            return []

        chunks: List[ChunkData] = []
        n = len(segments)
        i = 0
        chunk_idx = 0

        while i < n:
            current_segments: List[TranscriptSegment] = []
            word_count = 0
            j = i

            while j < n and (word_count < self.target_word_count or len(current_segments) == 0):
                seg = segments[j]
                current_segments.append(seg)
                word_count += len(seg.text.split())
                j += 1

            # Extract metadata
            speakers = list(dict.fromkeys([s.speaker for s in current_segments if s.speaker]))
            speaker_str = ", ".join(speakers) if speakers else "Speaker 1"
            
            # Format chunk text with speaker headers
            chunk_text = " ".join([f"{s.speaker}: {s.text}" for s in current_segments])
            start_time = current_segments[0].start_time
            end_time = current_segments[-1].end_time

            chunk = ChunkData(
                chunk_index=chunk_idx,
                text=chunk_text,
                speaker=speaker_str,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "segment_count": len(current_segments),
                    "start_time": start_time,
                    "end_time": end_time,
                    "speakers": speakers,
                },
            )
            chunks.append(chunk)
            chunk_idx += 1

            # Advance index with overlap
            if j >= n:
                break
            step = max(1, len(current_segments) - self.min_segment_overlap)
            i += step

        return chunks


transcript_chunker = TranscriptChunker()
