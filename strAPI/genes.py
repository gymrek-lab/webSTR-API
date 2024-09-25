from . repeats.models import Gene, Transcript

#genebuffer set in webstr codeto remove redundancy 

def get_exons_by_transcript(db, cds_only, transcript_obj):
    exons = []
    for exon in transcript_obj.exons:
        if cds_only and not exon.cds:
            continue
        exons.append(exon)
    
    if transcript_obj.gene.strand == "+":
        return list(sorted(exons, key=lambda x : x.start))
    elif transcript_obj.gene.strand == "-":
        return list(sorted(exons, key=lambda x : x.start, reverse=True))

def get_gene_info(db, gene_names, ensembl_ids, region_query):
    genes = []
    if gene_names:
        genes = db.query(Gene).filter(Gene.name.in_(gene_names)).all()
    elif ensembl_ids:
        genes =  db.query(Gene).filter(Gene.ensembl_id.in_(ensembl_ids)).all()  
    # Example chr1:182393-1014541
  
    elif region_query: 
        region_split = region_query.split(':')
        chrom = 'chr' + region_split[0]
        coord_split = region_split[1].split('-')
        start = int(coord_split[0])
        end = int(coord_split[1])

   
        genes = db.query(Gene).where(
            Gene.chr == chrom,
            Gene.end >= start,  # include genes that overlap @ start
            Gene.start <= end  # include genes that overlap @ end
        ).all()
    
    return genes

def get_genes_with_exons(db, genes):

    genes_exons = []
    for gene in iter(genes):
        transcripts = db.query(Transcript).filter_by(gene_id=gene.id).all()

        all_exons = []
        for transcript in transcripts:
            exons_obj = get_exons_by_transcript(db, False, transcript)


            exons = []
            for exon in iter(exons_obj):
                exons.append({
                    "ensembl_exon": exon.ensembl_exon,
                    "start":  exon.start,
                    "end":  exon.end,
                    "cds": exon.cds
                })
            all_exons.extend(exons)

   
    
        genes_exons.append({
            "ensembl_id": gene.ensembl_id,
            "start":  gene.start,
            "end":  gene.end,
            "chr": gene.chr,
            "strand": gene.strand,
            "name": gene.name,
            "description": gene.description,
            "exons": all_exons
        })
        
    return genes_exons         
