from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    key: str
    label: str
    specialty: str
    lay_symptoms: tuple[str, ...]
    clinical_symptoms: tuple[str, ...]
    exam_findings: tuple[str, ...]
    impressions: tuple[str, ...]
    plans: tuple[str, ...]
    imaging_findings: tuple[str, ...]
    lab_findings: tuple[str, ...]
    negations: tuple[str, ...] = ()
    distractor_keys: tuple[str, ...] = ()


CONDITIONS: tuple[Condition, ...] = (
    Condition(
        key="migraine_with_aura",
        label="Migraine with aura",
        specialty="Neurology",
        lay_symptoms=(
            "recurring headaches that start with flashing lights, followed by nausea and sensitivity to light",
            "throbbing one-sided headaches preceded by shimmering zigzag patterns in vision",
            "severe headaches with blind spots beforehand, then vomiting and needing a dark room",
        ),
        clinical_symptoms=(
            "recurrent unilateral cephalalgia preceded by a scintillating scotoma lasting twenty to thirty minutes",
            "episodic pulsatile hemicranial pain with preceding visual aura, photophobia, phonophobia, and emesis",
            "stereotyped visual prodrome followed within the hour by moderate to severe throbbing headache",
            "attacks aggravated by routine physical activity and relieved by rest in a darkened environment",
        ),
        exam_findings=(
            "cranial nerves II through XII intact, fundoscopy without papilloedema",
            "no focal neurological deficit between attacks, gait and coordination normal",
            "neck supple, no meningism, temporal arteries non-tender",
        ),
        impressions=(
            "Migraine with typical visual aura, episodic pattern, meeting ICHD criteria",
            "Aura-predominant migraine with rising attack frequency over the past two quarters",
        ),
        plans=(
            "Commence triptan at aura resolution rather than at onset; document response in a headache diary",
            "Discuss prophylaxis given attack frequency above four per month; review in eight weeks",
            "Advise on trigger identification including sleep debt, skipped meals, and alcohol",
        ),
        imaging_findings=(
            "No acute intracranial abnormality. No mass effect, midline shift, or restricted diffusion.",
            "Unremarkable parenchyma for age. No white matter lesion burden beyond expected.",
        ),
        lab_findings=(
            "Full blood count, renal panel, and inflammatory markers within reference limits",
            "ESR 8 mm/h, excluding an inflammatory cause for new headache in this age group",
        ),
        negations=(
            "Denies visual aura, unilateral features, or nausea with these headaches.",
            "No history of migraine. Headaches are bilateral and pressure-like without prodrome.",
        ),
        distractor_keys=("tension_headache", "cluster_headache"),
    ),
    Condition(
        key="tension_headache",
        label="Tension-type headache",
        specialty="Primary Care",
        lay_symptoms=(
            "a tight band of pressure around the head most days, worse by the evening",
            "constant dull head pain with a stiff neck and sore shoulders",
        ),
        clinical_symptoms=(
            "bilateral non-pulsatile pressing cephalalgia of mild to moderate intensity without aura",
            "chronic daily headache without photophobia, phonophobia, or autonomic features",
            "pericranial muscle tenderness with symptoms tracking workstation posture and stress load",
        ),
        exam_findings=(
            "marked tenderness over trapezius and suboccipital musculature, neurological examination normal",
            "no papilloedema, no focal deficit, cervical range of movement mildly restricted",
        ),
        impressions=(
            "Chronic tension-type headache with a musculoskeletal and ergonomic contribution",
            "Frequent episodic tension-type headache; no red flags for secondary cause",
        ),
        plans=(
            "Limit simple analgesia to two days per week to avoid medication overuse headache",
            "Refer to physiotherapy for cervical and scapular conditioning; workstation assessment advised",
        ),
        imaging_findings=(
            "No intracranial abnormality identified. Paranasal sinuses clear.",
        ),
        lab_findings=("Screening bloods unremarkable; thyroid function normal",),
        negations=(
            "Explicitly no visual disturbance, no vomiting, and no unilateral throbbing component.",
        ),
        distractor_keys=("migraine_with_aura", "cluster_headache"),
    ),
    Condition(
        key="cluster_headache",
        label="Cluster headache",
        specialty="Neurology",
        lay_symptoms=(
            "excruciating stabbing pain behind one eye at the same time each night, with a watering eye and blocked nose",
            "attacks of boring pain around one eye lasting under an hour, several times a day for weeks",
        ),
        clinical_symptoms=(
            "strictly unilateral periorbital pain of severe intensity with ipsilateral lacrimation, conjunctival injection, and rhinorrhoea",
            "circadian clustering of short-lived attacks with marked restlessness and agitation during episodes",
        ),
        exam_findings=(
            "partial ipsilateral ptosis and miosis noted during an observed attack, resolving between attacks",
            "no papilloedema; cranial nerve examination otherwise intact",
        ),
        impressions=(
            "Episodic cluster headache, currently in bout",
            "Trigeminal autonomic cephalalgia consistent with cluster headache",
        ),
        plans=(
            "High-flow oxygen for acute attacks; commence verapamil for bout suppression with ECG monitoring",
            "Avoid alcohol entirely during bouts; provide attack diary and safety-netting advice",
        ),
        imaging_findings=(
            "Pituitary and cavernous sinus unremarkable. No secondary cause for a trigeminal autonomic cephalalgia.",
        ),
        lab_findings=(
            "Baseline biochemistry acceptable prior to commencing verapamil",
        ),
        distractor_keys=("migraine_with_aura", "tension_headache"),
    ),
    Condition(
        key="type2_diabetes",
        label="Type 2 diabetes mellitus",
        specialty="Endocrinology",
        lay_symptoms=(
            "persistent thirst, needing to pass urine frequently, and blurry vision",
            "drinking constantly, up several times a night to urinate, and unexplained weight loss",
            "always thirsty, tired all the time, and slow-healing cuts",
        ),
        clinical_symptoms=(
            "polydipsia and polyuria over the preceding three weeks with intermittent blurred vision",
            "osmotic symptoms with nocturia four times nightly and unintentional weight loss of four kilograms",
            "hyperglycaemia confirmed on fingerstick testing with an elevated glycated haemoglobin",
            "central adiposity with acanthosis nigricans suggesting established insulin resistance",
        ),
        exam_findings=(
            "BMI 31.4, waist circumference 106 cm, acanthosis nigricans at the posterior neck",
            "peripheral pulses palpable, monofilament sensation intact at all ten sites",
            "no ketotic breath, hydration adequate, no postural drop",
        ),
        impressions=(
            "Newly diagnosed type 2 diabetes mellitus with osmotic symptoms and no evidence of ketosis",
            "Type 2 diabetes mellitus with suboptimal glycaemic control on current therapy",
        ),
        plans=(
            "Commence metformin with weekly dose escalation; structured education referral placed",
            "Baseline retinal screening and urinary albumin-to-creatinine ratio requested",
            "Review glycated haemoglobin in three months; home glucose monitoring commenced",
        ),
        imaging_findings=(
            "Hepatic steatosis noted incidentally. No focal hepatic lesion.",
        ),
        lab_findings=(
            "Glycated haemoglobin 9.1 percent, fasting plasma glucose 12.8 mmol/L, ketones negative",
            "Random plasma glucose 15.2 mmol/L with normal serum sodium and osmolality",
            "Urinary albumin-to-creatinine ratio 4.1 mg/mmol, estimated GFR 88 mL/min/1.73 m2",
        ),
        negations=(
            "Denies polyuria and polydipsia. Glucose checked incidentally and within range.",
        ),
        distractor_keys=(
            "diabetes_insipidus",
            "diabetic_peripheral_neuropathy",
            "chronic_kidney_disease",
        ),
    ),
    Condition(
        key="diabetes_insipidus",
        label="Cranial diabetes insipidus",
        specialty="Endocrinology",
        lay_symptoms=(
            "passing enormous volumes of very pale urine and unquenchable thirst, craving iced water",
            "urinating every hour day and night, drinking more than five litres daily",
        ),
        clinical_symptoms=(
            "polyuria exceeding four litres daily with polydipsia and a strong preference for chilled fluids",
            "hypotonic polyuria with inappropriately dilute urine despite rising serum sodium",
            "normoglycaemic osmotic-pattern symptoms with no glycosuria on dipstick",
        ),
        exam_findings=(
            "mucous membranes dry, weight down 2 kg, visual fields full to confrontation",
            "no acanthosis nigricans, BMI 23.1, no peripheral oedema",
        ),
        impressions=(
            "Cranial diabetes insipidus confirmed on water deprivation testing with desmopressin response",
            "Hypotonic polyuria consistent with partial cranial diabetes insipidus",
        ),
        plans=(
            "Commence desmopressin with sodium monitoring at day three and day seven",
            "Pituitary imaging requested to exclude an infiltrative or structural lesion",
        ),
        imaging_findings=(
            "Loss of the posterior pituitary bright spot. Infundibulum mildly thickened.",
        ),
        lab_findings=(
            "Serum sodium 148 mmol/L, serum osmolality 302 mOsm/kg, urine osmolality 118 mOsm/kg, glucose 5.1 mmol/L",
            "Glycated haemoglobin 5.2 percent, excluding diabetes mellitus as the cause of polyuria",
        ),
        distractor_keys=("type2_diabetes", "chronic_kidney_disease"),
    ),
    Condition(
        key="diabetic_peripheral_neuropathy",
        label="Diabetic peripheral neuropathy",
        specialty="Neurology",
        lay_symptoms=(
            "burning pain in both feet that is worst at night, with numbness and pins and needles",
            "feet feel like they are on fire in bed, and I cannot feel the floor properly",
            "electric shooting pains in the toes and numb soles that make walking feel unsteady",
        ),
        clinical_symptoms=(
            "symmetrical distal burning dysaesthesia in a stocking distribution with nocturnal exacerbation",
            "length-dependent sensory polyneuropathy with reduced vibration and pinprick sensation to the mid-shin",
            "allodynia to light touch over the dorsum of both feet with absent ankle reflexes",
        ),
        exam_findings=(
            "monofilament sensation absent at six of ten plantar sites bilaterally, ankle jerks absent",
            "vibration sense reduced to the tibial tuberosity, proprioception impaired at the great toe",
            "no ulceration, but callus formation over both metatarsal heads with dry skin",
        ),
        impressions=(
            "Painful diabetic peripheral neuropathy with high-risk feet requiring podiatry surveillance",
            "Length-dependent sensory neuropathy secondary to long-standing diabetes mellitus",
        ),
        plans=(
            "Commence duloxetine, titrating over two weeks; review analgesic benefit and tolerability",
            "Urgent podiatry referral for high-risk foot protection and offloading footwear",
            "Reinforce daily foot inspection and glycaemic optimisation",
        ),
        imaging_findings=(
            "No Charcot change. Plantar soft tissues intact without collection.",
        ),
        lab_findings=(
            "Glycated haemoglobin 8.7 percent, vitamin B12 341 ng/L, thyroid function normal",
            "Nerve conduction studies show reduced sural sensory amplitudes with preserved motor conduction velocity",
        ),
        distractor_keys=("type2_diabetes", "lumbar_radiculopathy"),
    ),
    Condition(
        key="heart_failure",
        label="Heart failure with reduced ejection fraction",
        specialty="Cardiology",
        lay_symptoms=(
            "breathless walking to the letterbox and both ankles swollen by evening",
            "cannot lie flat without getting short of breath, waking gasping, legs puffy",
            "shortness of breath with swelling in both legs and rapid weight gain this fortnight",
        ),
        clinical_symptoms=(
            "exertional dyspnoea at NYHA class III with orthopnoea requiring three pillows and paroxysmal nocturnal dyspnoea",
            "bilateral pitting pedal oedema to mid-calf with a three kilogram weight gain over ten days",
            "reduced exercise tolerance with early satiety and abdominal fullness from congestion",
        ),
        exam_findings=(
            "elevated jugular venous pressure at 7 cm, bibasal inspiratory crepitations, displaced apex beat",
            "pitting oedema to mid-calf bilaterally, tender hepatic edge, third heart sound audible",
            "blood pressure 106/68, heart rate 96 regular, oxygen saturation 94 percent on room air",
        ),
        impressions=(
            "Decompensated heart failure with reduced ejection fraction and clear volume overload",
            "Heart failure with reduced ejection fraction, ischaemic aetiology, currently congested",
        ),
        plans=(
            "Commence intravenous furosemide with daily weights and strict fluid balance",
            "Optimise quadruple therapy as blood pressure permits; heart failure nurse review arranged",
            "Fluid restriction to 1.5 litres daily with dietary sodium counselling",
        ),
        imaging_findings=(
            "Cardiomegaly with pulmonary venous congestion and small bilateral pleural effusions.",
            "Echocardiography demonstrates left ventricular ejection fraction of 32 percent with global hypokinesis.",
        ),
        lab_findings=(
            "NT-proBNP 3820 ng/L, creatinine 118 umol/L, sodium 134 mmol/L",
            "Troponin marginally elevated without a dynamic rise, consistent with strain rather than infarction",
        ),
        negations=(
            "No peripheral oedema and no orthopnoea. Breathlessness is purely exertional and wheeze-predominant.",
        ),
        distractor_keys=("copd", "atrial_fibrillation", "chronic_kidney_disease"),
    ),
    Condition(
        key="copd",
        label="Chronic obstructive pulmonary disease",
        specialty="Respiratory",
        lay_symptoms=(
            "breathless on the stairs with a morning cough bringing up phlegm most days",
            "getting winded easily, chesty cough every winter, forty years of smoking",
        ),
        clinical_symptoms=(
            "progressive exertional breathlessness with chronic productive cough and recurrent winter exacerbations",
            "airflow obstruction that is incompletely reversible on post-bronchodilator spirometry",
            "prolonged expiratory phase with hyperinflation and reduced breath sounds throughout",
        ),
        exam_findings=(
            "barrel-shaped chest, hyperresonant percussion, diffusely reduced air entry with expiratory wheeze",
            "no peripheral oedema, jugular venous pressure not elevated, tar staining of the fingers",
        ),
        impressions=(
            "COPD GOLD group B with an exacerbation-prone phenotype",
            "Moderate airflow obstruction consistent with COPD; smoking remains the dominant driver",
        ),
        plans=(
            "Escalate to dual long-acting bronchodilator therapy and confirm inhaler technique",
            "Pulmonary rehabilitation referral and smoking cessation pharmacotherapy offered",
        ),
        imaging_findings=(
            "Hyperinflated lungs with flattened hemidiaphragms and paucity of basal vascular markings. No effusion.",
        ),
        lab_findings=(
            "Post-bronchodilator FEV1 54 percent predicted with FEV1/FVC ratio of 0.58",
            "Alpha-1 antitrypsin within normal limits; eosinophil count 0.18 x10^9/L",
        ),
        distractor_keys=("heart_failure", "exercise_induced_asthma"),
    ),
    Condition(
        key="atrial_fibrillation",
        label="Atrial fibrillation",
        specialty="Cardiology",
        lay_symptoms=(
            "heart racing and thumping irregularly with light-headedness and breathlessness",
            "fluttering in the chest that comes and goes, feeling faint and short of breath",
        ),
        clinical_symptoms=(
            "irregularly irregular palpitations with associated presyncope and exertional dyspnoea",
            "paroxysmal episodes lasting hours with spontaneous termination and no chest pain",
        ),
        exam_findings=(
            "pulse irregularly irregular at 128, apical-radial deficit present, no murmur",
            "no signs of volume overload, jugular venous pressure normal, chest clear",
        ),
        impressions=(
            "Newly detected atrial fibrillation with rapid ventricular response",
            "Paroxysmal atrial fibrillation with a CHA2DS2-VASc score of 3",
        ),
        plans=(
            "Commence rate control with bisoprolol and start anticoagulation after bleeding-risk discussion",
            "Thyroid function and echocardiography requested; ambulatory monitoring to quantify burden",
        ),
        imaging_findings=(
            "Left atrial dilatation with preserved left ventricular systolic function.",
        ),
        lab_findings=(
            "Thyroid stimulating hormone suppressed at 0.08 mIU/L, prompting endocrine review",
            "Electrolytes and magnesium within range; renal function adequate for direct oral anticoagulation",
        ),
        distractor_keys=("heart_failure",),
    ),
    Condition(
        key="exercise_induced_asthma",
        label="Exercise-induced bronchoconstriction",
        specialty="Respiratory",
        lay_symptoms=(
            "chest tightness and wheezing that comes on during exercise, especially in cold air",
            "wheezy and tight-chested about ten minutes into running, settles with rest",
            "coughing and whistling in the chest during sport but fine the rest of the time",
        ),
        clinical_symptoms=(
            "bronchoconstriction developing several minutes after the onset of exertion with expiratory wheeze and chest tightness",
            "exertional symptoms provoked by cold dry air and resolving spontaneously within thirty minutes of rest",
            "reversible airflow limitation with a 14 percent fall in FEV1 following an exercise challenge",
        ),
        exam_findings=(
            "chest clear at rest, peak expiratory flow 88 percent of personal best, no accessory muscle use",
            "scattered expiratory wheeze audible immediately post-exercise, resolving at ten minutes",
        ),
        impressions=(
            "Exercise-induced bronchoconstriction on a background of atopy, currently undertreated",
            "Mild intermittent asthma with a predominantly exercise-triggered pattern",
        ),
        plans=(
            "Pre-exercise short-acting beta agonist ten minutes prior; commence low-dose inhaled corticosteroid",
            "Provide written asthma action plan; review inhaler technique and adherence in six weeks",
            "Advise graded warm-up and nasal breathing in cold conditions",
        ),
        imaging_findings=(
            "Lungs clear. No hyperinflation, focal consolidation, or pleural abnormality.",
        ),
        lab_findings=(
            "Spirometry shows 15 percent FEV1 reversibility post-bronchodilator; fractional exhaled nitric oxide 42 ppb",
            "Total IgE elevated at 318 kU/L with positive house dust mite specific IgE",
        ),
        negations=(
            "No wheeze and no exertional component; breathlessness is continuous and unrelated to activity.",
        ),
        distractor_keys=("copd", "allergic_rhinitis", "heart_failure"),
    ),
    Condition(
        key="cholelithiasis",
        label="Symptomatic cholelithiasis with biliary obstruction",
        specialty="General Surgery",
        lay_symptoms=(
            "yellowing of the eyes with severe pain in the upper right side of the abdomen after fatty meals",
            "the whites of my eyes went yellow, my urine turned dark, and I get gripping pain under the right ribs",
            "intense pain below the right ribcage spreading to my shoulder blade, with jaundice and itching",
        ),
        clinical_symptoms=(
            "scleral icterus with right upper quadrant colic radiating to the right scapula, provoked by fatty meals",
            "postprandial biliary colic with obstructive jaundice, dark urine, and pale stools",
            "episodic severe right hypochondrial pain lasting several hours with associated pruritus",
        ),
        exam_findings=(
            "tender right upper quadrant with a positive Murphy sign, scleral icterus evident, no peritonism",
            "afebrile, no palpable gallbladder, no organomegaly, excoriations from scratching noted",
        ),
        impressions=(
            "Symptomatic cholelithiasis with choledocholithiasis causing obstructive jaundice",
            "Biliary colic with a cholestatic liver profile; stone in the common bile duct suspected",
        ),
        plans=(
            "Fast the patient, commence intravenous fluids, and refer for urgent ERCP",
            "Interval laparoscopic cholecystectomy once biliary decompression is achieved",
        ),
        imaging_findings=(
            "Multiple mobile gallstones with a dilated common bile duct measuring 11 mm and an obstructing distal calculus.",
            "Gallbladder wall thickening to 5 mm with pericholecystic fluid. Intrahepatic duct dilatation present.",
        ),
        lab_findings=(
            "Bilirubin 84 umol/L, alkaline phosphatase 412 U/L, gamma-glutamyl transferase 508 U/L, ALT 132 U/L",
            "Cholestatic liver enzyme pattern with normal lipase, arguing against pancreatitis",
        ),
        distractor_keys=("gerd", "urinary_tract_infection"),
    ),
    Condition(
        key="gerd",
        label="Gastro-oesophageal reflux disease",
        specialty="Gastroenterology",
        lay_symptoms=(
            "burning behind the breastbone after meals with acid coming up into my throat at night",
            "heartburn most evenings, worse lying down, with a sour taste and hoarse voice",
        ),
        clinical_symptoms=(
            "retrosternal burning with acid regurgitation, worse when supine and after large meals",
            "postprandial dyspepsia with nocturnal reflux and intermittent hoarseness",
        ),
        exam_findings=(
            "epigastric tenderness without guarding, no right upper quadrant tenderness, no jaundice",
            "no mass, no lymphadenopathy, weight stable",
        ),
        impressions=(
            "Gastro-oesophageal reflux disease without alarm features",
            "Reflux-predominant dyspepsia; no indication for urgent endoscopy",
        ),
        plans=(
            "Eight-week proton pump inhibitor trial with weight and late-meal advice, then step-down review",
            "Test and treat for Helicobacter pylori if symptoms persist after the initial trial",
        ),
        imaging_findings=(
            "Gallbladder normal with no calculus. Common bile duct not dilated. Liver echotexture normal.",
        ),
        lab_findings=(
            "Liver function tests entirely normal, notably with a normal bilirubin and alkaline phosphatase",
            "Helicobacter pylori stool antigen negative; full blood count normal",
        ),
        negations=(
            "No jaundice, no pale stools, and no radiation to the shoulder. Liver enzymes are normal.",
        ),
        distractor_keys=("cholelithiasis",),
    ),
    Condition(
        key="hypertension",
        label="Essential hypertension",
        specialty="Primary Care",
        lay_symptoms=(
            "no symptoms, high readings picked up at the pharmacy",
            "occasional morning headaches with consistently high home readings",
        ),
        clinical_symptoms=(
            "stage 2 hypertension confirmed on ambulatory monitoring with a blunted nocturnal dip",
            "elevated clinic and home blood pressure readings without end-organ symptoms",
        ),
        exam_findings=(
            "blood pressure 158/96 seated after five minutes rest, repeated at 156/94",
            "no radiofemoral delay, no renal bruit, fundoscopy without hypertensive retinopathy",
        ),
        impressions=(
            "Essential hypertension, stage 2, with a ten-year cardiovascular risk of 14 percent",
            "Newly confirmed hypertension without evidence of a secondary cause",
        ),
        plans=(
            "Commence an ACE inhibitor with renal function and electrolytes at two weeks",
            "Lifestyle counselling on sodium reduction and aerobic activity; home monitoring diary issued",
        ),
        imaging_findings=(
            "No left ventricular hypertrophy. Aortic root dimensions normal.",
        ),
        lab_findings=(
            "Estimated GFR 82 mL/min/1.73 m2, potassium 4.2 mmol/L, urinary albumin-to-creatinine ratio normal",
            "Aldosterone-to-renin ratio not suggestive of primary hyperaldosteronism",
        ),
        distractor_keys=("chronic_kidney_disease",),
    ),
    Condition(
        key="hypothyroidism",
        label="Primary hypothyroidism",
        specialty="Endocrinology",
        lay_symptoms=(
            "exhausted all the time, cold when nobody else is, constipated, and gaining weight",
            "dry skin, thinning hair, low mood, and sluggish thinking for months",
        ),
        clinical_symptoms=(
            "insidious fatigue with cold intolerance, constipation, and weight gain despite unchanged intake",
            "dry coarse skin, bradycardia, and delayed relaxation of the ankle reflexes",
        ),
        exam_findings=(
            "pulse 54 regular, dry skin, periorbital puffiness, no palpable goitre",
            "slow-relaxing ankle reflexes bilaterally, no proximal weakness",
        ),
        impressions=(
            "Overt primary hypothyroidism, likely autoimmune given positive antibodies",
            "Primary hypothyroidism with symptom burden warranting replacement",
        ),
        plans=(
            "Commence levothyroxine weight-based; recheck thyroid function in six weeks before adjusting",
            "Counsel on fasted administration and separation from calcium and iron supplements",
        ),
        imaging_findings=(
            "Thyroid heterogeneous with reduced echogenicity, no discrete nodule.",
        ),
        lab_findings=(
            "Thyroid stimulating hormone 22.4 mIU/L with free T4 8.1 pmol/L and positive TPO antibodies",
            "Lipid panel shows total cholesterol 6.8 mmol/L, expected to improve with replacement",
        ),
        distractor_keys=("iron_deficiency_anemia", "major_depressive_pattern"),
    ),
    Condition(
        key="iron_deficiency_anemia",
        label="Iron deficiency anaemia",
        specialty="Haematology",
        lay_symptoms=(
            "worn out and breathless climbing stairs, looking pale, craving ice",
            "dizzy on standing, pounding heart, heavy periods for the last year",
        ),
        clinical_symptoms=(
            "progressive exertional fatigue and dyspnoea with pallor and pica for ice",
            "microcytic hypochromic anaemia in the context of menorrhagia",
        ),
        exam_findings=(
            "conjunctival pallor, koilonychia, angular stomatitis, no lymphadenopathy",
            "resting tachycardia at 104, soft ejection systolic flow murmur, no splenomegaly",
        ),
        impressions=(
            "Iron deficiency anaemia secondary to menorrhagia, symptomatic",
            "Microcytic anaemia with depleted iron stores requiring replacement and source investigation",
        ),
        plans=(
            "Commence oral iron on alternate days to improve absorption; recheck full blood count at four weeks",
            "Gynaecology referral for menorrhagia; coeliac serology sent",
        ),
        imaging_findings=(
            "No hepatosplenomegaly. No intra-abdominal mass identified.",
        ),
        lab_findings=(
            "Haemoglobin 89 g/L, MCV 71 fL, ferritin 6 ug/L, transferrin saturation 8 percent",
            "Coeliac serology negative; faecal immunochemical test negative",
        ),
        distractor_keys=("hypothyroidism", "chronic_kidney_disease"),
    ),
    Condition(
        key="lumbar_radiculopathy",
        label="Lumbar radiculopathy",
        specialty="Orthopaedics",
        lay_symptoms=(
            "shooting pain from the lower back down the back of one leg into the foot, with numb toes",
            "electric pain down the left leg when I cough or sit for long, with a weak ankle",
        ),
        clinical_symptoms=(
            "unilateral radicular pain in an L5 distribution with dermatomal paraesthesia and dorsiflexion weakness",
            "positive straight leg raise at forty degrees with pain reproduced on Valsalva",
        ),
        exam_findings=(
            "straight leg raise positive at 40 degrees on the left, ankle dorsiflexion 4 out of 5, reduced L5 sensation",
            "no saddle anaesthesia, anal tone normal, bladder function preserved",
        ),
        impressions=(
            "Left L5 radiculopathy secondary to a paracentral disc protrusion, no red flags",
            "Lumbar radiculopathy with a mild motor deficit suitable for conservative management",
        ),
        plans=(
            "Neuropathic analgesia with structured physiotherapy; review motor function in four weeks",
            "Safety-net for cauda equina symptoms with written escalation advice",
        ),
        imaging_findings=(
            "Left paracentral disc protrusion at L4-L5 with contact upon the traversing L5 nerve root. No cord compression.",
        ),
        lab_findings=(
            "Inflammatory markers normal, excluding an infective or inflammatory cause",
        ),
        distractor_keys=("diabetic_peripheral_neuropathy", "osteoarthritis_knee"),
    ),
    Condition(
        key="osteoarthritis_knee",
        label="Knee osteoarthritis",
        specialty="Orthopaedics",
        lay_symptoms=(
            "deep ache in both knees worse after walking, stiff for ten minutes when I get up",
            "knees grind and give way on stairs, swelling after gardening",
        ),
        clinical_symptoms=(
            "activity-related knee pain with short-lived morning stiffness and crepitus on movement",
            "mechanical symptoms with effusion after loading and reduced flexion range",
        ),
        exam_findings=(
            "bilateral crepitus, small effusion on the right, flexion limited to 110 degrees, varus alignment",
            "no erythema, no warmth, ligamentous examination stable",
        ),
        impressions=(
            "Bilateral tricompartmental knee osteoarthritis, right worse than left",
            "Symptomatic knee osteoarthritis with a functional impact on stairs and gardening",
        ),
        plans=(
            "Structured quadriceps strengthening, weight management support, topical NSAID trial",
            "Consider arthroplasty discussion if function deteriorates despite conservative measures",
        ),
        imaging_findings=(
            "Medial joint space narrowing with subchondral sclerosis and marginal osteophytes. No acute fracture.",
        ),
        lab_findings=(
            "Inflammatory markers normal; urate within range, arguing against a crystal arthropathy",
        ),
        distractor_keys=("lumbar_radiculopathy",),
    ),
    Condition(
        key="community_acquired_pneumonia",
        label="Community-acquired pneumonia",
        specialty="Respiratory",
        lay_symptoms=(
            "fever with shaking chills, a cough bringing up rusty phlegm, and sharp pain breathing in",
            "high temperature, wet cough, and a stabbing pain in the right side of the chest",
        ),
        clinical_symptoms=(
            "acute febrile illness with productive cough, pleuritic chest pain, and focal breathlessness",
            "rigors and purulent sputum with focal consolidation on examination",
        ),
        exam_findings=(
            "temperature 38.9, respiratory rate 24, coarse crackles and bronchial breathing at the right base",
            "oxygen saturation 93 percent on room air, dull percussion note at the right base",
        ),
        impressions=(
            "Community-acquired pneumonia, CURB-65 score of 1, suitable for ambulatory management",
            "Right basal community-acquired pneumonia with adequate oxygenation",
        ),
        plans=(
            "Commence amoxicillin for five days with a safety-net review at forty-eight hours",
            "Repeat chest radiograph at six weeks to confirm radiological resolution",
        ),
        imaging_findings=(
            "Right lower lobe consolidation with air bronchograms. Small ipsilateral pleural reaction. No cavitation.",
        ),
        lab_findings=(
            "C-reactive protein 148 mg/L, white cell count 15.2 x10^9/L with neutrophilia, urea 6.1 mmol/L",
            "Blood cultures negative at 48 hours; pneumococcal urinary antigen positive",
        ),
        distractor_keys=("copd", "heart_failure"),
    ),
    Condition(
        key="allergic_rhinitis",
        label="Allergic rhinitis",
        specialty="Primary Care",
        lay_symptoms=(
            "blocked itchy nose, sneezing fits, and watery eyes every spring",
            "constant nasal congestion, post-nasal drip, and an itchy throat",
        ),
        clinical_symptoms=(
            "seasonal nasal obstruction with paroxysmal sneezing, rhinorrhoea, and conjunctival irritation",
            "perennial rhinitis with a pollen-driven seasonal exacerbation and disturbed sleep",
        ),
        exam_findings=(
            "pale boggy nasal mucosa with clear secretions, no polyps visible, transverse nasal crease",
            "chest clear, no wheeze, tympanic membranes normal",
        ),
        impressions=(
            "Moderate persistent allergic rhinitis with a seasonal component",
            "Allergic rhinitis contributing to sleep disruption and daytime fatigue",
        ),
        plans=(
            "Intranasal corticosteroid with technique demonstration; add an oral antihistamine during peak season",
            "Allergen avoidance advice; consider immunotherapy referral if inadequately controlled",
        ),
        imaging_findings=(
            "Mild mucosal thickening of the maxillary sinuses. No fluid level or bony erosion.",
        ),
        lab_findings=(
            "Specific IgE positive for grass pollen and house dust mite; eosinophils 0.42 x10^9/L",
        ),
        distractor_keys=("exercise_induced_asthma",),
    ),
    Condition(
        key="obstructive_sleep_apnea",
        label="Obstructive sleep apnoea",
        specialty="Respiratory",
        lay_symptoms=(
            "loud snoring with my partner seeing me stop breathing, and falling asleep at my desk",
            "waking unrefreshed with a dry mouth and morning headaches, dozing off while driving",
        ),
        clinical_symptoms=(
            "witnessed apnoeas with habitual snoring and excessive daytime somnolence",
            "non-restorative sleep with an Epworth Sleepiness Scale score of 15",
        ),
        exam_findings=(
            "BMI 34.8, neck circumference 44 cm, Mallampati class III, crowded oropharynx",
            "blood pressure 146/92, no peripheral oedema, chest clear",
        ),
        impressions=(
            "Moderate obstructive sleep apnoea with significant daytime somnolence",
            "Obstructive sleep apnoea contributing to resistant hypertension",
        ),
        plans=(
            "Commence CPAP with a mask-fitting appointment and adherence review at six weeks",
            "Mandatory advice regarding driving safety given somnolence; weight management referral",
        ),
        imaging_findings=(
            "Upper airway crowding without a discrete obstructing lesion.",
        ),
        lab_findings=(
            "Overnight oximetry demonstrates an apnoea-hypopnoea index of 24 with nadir saturation of 84 percent",
            "Thyroid function normal; haematocrit 0.48",
        ),
        distractor_keys=("hypothyroidism", "hypertension"),
    ),
    Condition(
        key="chronic_kidney_disease",
        label="Chronic kidney disease stage 3b",
        specialty="Nephrology",
        lay_symptoms=(
            "tired with itchy skin, puffy ankles in the evening, and passing urine more at night",
            "poor appetite, metallic taste, cramps at night, and reduced energy",
        ),
        clinical_symptoms=(
            "declining renal function with nocturia, pruritus, and mild peripheral oedema",
            "uraemic symptoms with anorexia and nocturnal cramps on a background of proteinuria",
        ),
        exam_findings=(
            "blood pressure 152/88, mild pitting ankle oedema, no uraemic flap, no rub",
            "excoriations over the forearms, no palpable bladder, no renal bruit",
        ),
        impressions=(
            "Chronic kidney disease stage 3b with albuminuria, likely diabetic and hypertensive in origin",
            "Progressive chronic kidney disease requiring nephrology co-management",
        ),
        plans=(
            "Optimise renin-angiotensin blockade and add an SGLT2 inhibitor for renal protection",
            "Avoid nephrotoxins including NSAIDs; provide sick-day medication guidance",
        ),
        imaging_findings=(
            "Both kidneys reduced in size with increased cortical echogenicity. No hydronephrosis or calculus.",
        ),
        lab_findings=(
            "Estimated GFR 36 mL/min/1.73 m2, creatinine 168 umol/L, urinary albumin-to-creatinine ratio 62 mg/mmol",
            "Haemoglobin 104 g/L with adequate iron stores, parathyroid hormone 14.8 pmol/L",
        ),
        distractor_keys=("type2_diabetes", "heart_failure", "hypertension"),
    ),
    Condition(
        key="urinary_tract_infection",
        label="Urinary tract infection",
        specialty="Primary Care",
        lay_symptoms=(
            "burning when passing urine, going constantly, and cloudy strong-smelling urine",
            "stinging on urination with lower belly pressure and a trace of blood",
        ),
        clinical_symptoms=(
            "dysuria with urinary frequency, urgency, and suprapubic discomfort",
            "lower urinary tract symptoms with malodorous cloudy urine and microscopic haematuria",
        ),
        exam_findings=(
            "suprapubic tenderness without loin pain, afebrile, no costovertebral angle tenderness",
            "observations stable, no systemic features of sepsis",
        ),
        impressions=(
            "Uncomplicated lower urinary tract infection",
            "Lower urinary tract infection without features of pyelonephritis",
        ),
        plans=(
            "Three-day course of nitrofurantoin with fluid advice and a safety-net for systemic features",
            "Send urine culture; review if symptoms persist beyond forty-eight hours",
        ),
        imaging_findings=(
            "No hydronephrosis or renal calculus. Bladder wall unremarkable.",
        ),
        lab_findings=(
            "Urine dipstick positive for nitrites and leucocytes; culture grew Escherichia coli sensitive to nitrofurantoin",
            "Renal function preserved; inflammatory markers only mildly elevated",
        ),
        distractor_keys=("type2_diabetes", "cholelithiasis"),
    ),
    Condition(
        key="major_depressive_pattern",
        label="Depressive episode",
        specialty="Mental Health",
        lay_symptoms=(
            "flat and hopeless for months, no interest in anything, waking at four every morning",
            "cannot concentrate, no appetite, feeling worthless and exhausted",
        ),
        clinical_symptoms=(
            "persistent low mood with anhedonia, early morning wakening, and impaired concentration",
            "depressive episode of moderate severity with reduced appetite and diurnal mood variation",
        ),
        exam_findings=(
            "reduced eye contact, slowed speech, mood objectively low, no active suicidal intent expressed",
            "no psychotic features, cognition grossly intact, safety plan documented",
        ),
        impressions=(
            "Moderate depressive episode without psychotic features; risk currently assessed as low",
            "Depressive episode with prominent somatic symptoms; organic screen advised",
        ),
        plans=(
            "Commence an SSRI with a review at two weeks for tolerability and emergent risk",
            "Refer for structured psychological therapy; document a collaborative safety plan",
        ),
        imaging_findings=("No structural intracranial abnormality.",),
        lab_findings=(
            "Thyroid function, full blood count, ferritin, and vitamin B12 all normal, excluding a common organic contributor",
        ),
        distractor_keys=("hypothyroidism", "iron_deficiency_anemia"),
    ),
)

FILLER_ONLY_CONDITIONS: tuple[Condition, ...] = (
    Condition(
        key="psoriasis",
        label="Chronic plaque psoriasis",
        specialty="Dermatology",
        lay_symptoms=(
            "thick scaly red patches on both elbows and knees that flake and itch",
            "silvery scaling on the scalp with cracked bleeding skin behind the ears",
        ),
        clinical_symptoms=(
            "well-demarcated erythematous plaques with silvery scale over extensor surfaces",
            "symmetrical plaque distribution with nail pitting and scalp involvement",
            "pruritus and fissuring with a clear seasonal pattern of deterioration",
        ),
        exam_findings=(
            "plaques over both elbows, knees, and sacrum covering roughly eight percent body surface area",
            "nail pitting and onycholysis of four fingernails, no joint swelling or tenderness",
        ),
        impressions=(
            "Chronic plaque psoriasis of moderate severity with nail involvement",
            "Plaque psoriasis with a significant quality-of-life impact",
        ),
        plans=(
            "Potent topical corticosteroid with a vitamin D analogue; review response at eight weeks",
            "Emollient use reinforced; screen for psoriatic arthritis at each review",
        ),
        imaging_findings=("No erosive change in the small joints of the hands.",),
        lab_findings=(
            "Inflammatory markers normal; liver function baseline acceptable prior to systemic therapy",
        ),
        distractor_keys=("atopic_dermatitis",),
    ),
    Condition(
        key="atopic_dermatitis",
        label="Atopic dermatitis",
        specialty="Dermatology",
        lay_symptoms=(
            "intensely itchy dry rash in the elbow creases and behind the knees, worse at night",
            "weeping cracked skin on the hands that stings with water",
        ),
        clinical_symptoms=(
            "flexural eczematous change with excoriation and lichenification",
            "chronic relapsing pruritic dermatitis on a background of personal atopy",
        ),
        exam_findings=(
            "ill-defined erythema with excoriation in both antecubital fossae and popliteal fossae",
            "no secondary bacterial infection, no pustulation, skin dry throughout",
        ),
        impressions=(
            "Moderate atopic dermatitis with a flare precipitated by soap contact",
            "Atopic dermatitis with sleep disturbance from nocturnal pruritus",
        ),
        plans=(
            "Step up to a moderately potent topical corticosteroid for two weeks, then taper",
            "Soap substitute and generous emollient; review technique and quantity used",
        ),
        imaging_findings=("Not applicable to this presentation.",),
        lab_findings=(
            "Total IgE elevated; no evidence of secondary infection on swab",
        ),
        distractor_keys=("psoriasis",),
    ),
    Condition(
        key="gout",
        label="Acute gout",
        specialty="Rheumatology",
        lay_symptoms=(
            "sudden agonising pain in the big toe overnight, red hot and too sore to touch",
            "the joint at the base of my toe swelled up and I cannot bear a sock on it",
        ),
        clinical_symptoms=(
            "acute monoarthritis of the first metatarsophalangeal joint with florid inflammation",
            "abrupt nocturnal onset of severe joint pain reaching peak intensity within hours",
            "podagra with overlying erythema and exquisite tenderness on palpation",
        ),
        exam_findings=(
            "first metatarsophalangeal joint hot, erythematous, and swollen with marked tenderness",
            "no other joint involvement, afebrile, no tophi identified",
        ),
        impressions=(
            "Acute gout affecting the first metatarsophalangeal joint",
            "Crystal arthropathy consistent with acute gout; septic arthritis considered unlikely",
        ),
        plans=(
            "Short course of an NSAID with gastric protection; rest and elevate the joint",
            "Defer urate-lowering therapy until the flare settles, then review prophylaxis",
        ),
        imaging_findings=(
            "Soft tissue swelling about the first metatarsophalangeal joint without erosion.",
        ),
        lab_findings=(
            "Serum urate 512 umol/L during the flare; renal function preserved",
        ),
        distractor_keys=("rheumatoid_arthritis", "ankle_sprain"),
    ),
    Condition(
        key="rheumatoid_arthritis",
        label="Rheumatoid arthritis",
        specialty="Rheumatology",
        lay_symptoms=(
            "stiff swollen fingers and wrists every morning for over an hour, both hands the same",
            "hands ache and grip is weak, cannot open jars, stiffness eases by midday",
        ),
        clinical_symptoms=(
            "symmetrical inflammatory polyarthritis of the small joints with prolonged early morning stiffness",
            "synovitis of the metacarpophalangeal and proximal interphalangeal joints bilaterally",
        ),
        exam_findings=(
            "boggy synovial swelling of the second and third metacarpophalangeal joints bilaterally",
            "grip strength reduced, no deformity, no rheumatoid nodules",
        ),
        impressions=(
            "Seropositive rheumatoid arthritis, early disease, requiring prompt disease-modifying therapy",
            "Inflammatory polyarthritis consistent with rheumatoid arthritis",
        ),
        plans=(
            "Urgent rheumatology referral; commence methotrexate with folic acid after baseline screening",
            "Assess disease activity score at each review; discuss joint protection with occupational therapy",
        ),
        imaging_findings=(
            "Periarticular osteopenia without frank erosion. Soft tissue swelling noted.",
        ),
        lab_findings=(
            "Rheumatoid factor positive, anti-CCP strongly positive, C-reactive protein 38 mg/L",
        ),
        distractor_keys=("gout",),
    ),
    Condition(
        key="benign_positional_vertigo",
        label="Benign paroxysmal positional vertigo",
        specialty="Primary Care",
        lay_symptoms=(
            "the room spins violently for under a minute when I roll over in bed or look up",
            "brief whirling dizziness triggered by turning my head, with nausea afterwards",
        ),
        clinical_symptoms=(
            "brief rotational vertigo provoked by positional change, lasting less than sixty seconds",
            "positional nystagmus reproduced on the Dix-Hallpike manoeuvre with characteristic latency",
        ),
        exam_findings=(
            "Dix-Hallpike positive on the right with rotatory nystagmus and subjective vertigo",
            "cranial nerves intact, no cerebellar signs, hearing subjectively normal",
        ),
        impressions=(
            "Right posterior canal benign paroxysmal positional vertigo",
            "Positional vertigo of peripheral origin; no red flags for a central cause",
        ),
        plans=(
            "Epley repositioning manoeuvre performed with instructions for home repetition",
            "Advise against driving while symptomatic; review in two weeks if unresolved",
        ),
        imaging_findings=(
            "No posterior fossa abnormality. Internal auditory canals unremarkable.",
        ),
        lab_findings=(
            "Screening bloods normal; no evidence of anaemia or electrolyte disturbance",
        ),
        distractor_keys=("generalised_anxiety",),
    ),
    Condition(
        key="generalised_anxiety",
        label="Generalised anxiety disorder",
        specialty="Mental Health",
        lay_symptoms=(
            "constant worry I cannot switch off, restless and on edge with a churning stomach",
            "tense all day, irritable, mind racing at bedtime so I cannot get to sleep",
        ),
        clinical_symptoms=(
            "excessive uncontrollable worry across multiple domains for more than six months",
            "psychomotor tension with initial insomnia, irritability, and impaired concentration",
        ),
        exam_findings=(
            "appears tense with fidgeting, speech normal in rate, no thought disorder",
            "no tremor, thyroid not enlarged, cardiovascular examination normal",
        ),
        impressions=(
            "Generalised anxiety disorder of moderate severity",
            "Generalised anxiety disorder with prominent sleep-onset difficulty",
        ),
        plans=(
            "Refer for cognitive behavioural therapy; discuss an SSRI if preference favours medication",
            "Sleep hygiene advice and a structured worry-time technique introduced",
        ),
        imaging_findings=("Not applicable to this presentation.",),
        lab_findings=(
            "Thyroid function normal, excluding hyperthyroidism as a contributor",
        ),
        distractor_keys=("benign_positional_vertigo",),
    ),
    Condition(
        key="acute_otitis_media",
        label="Acute otitis media",
        specialty="Primary Care",
        lay_symptoms=(
            "throbbing earache with muffled hearing and a temperature for two days",
            "sharp pain deep in the ear, then discharge and sudden relief",
        ),
        clinical_symptoms=(
            "unilateral otalgia with fever and conductive hearing loss following a coryzal illness",
            "bulging erythematous tympanic membrane with loss of the normal landmarks",
        ),
        exam_findings=(
            "right tympanic membrane erythematous and bulging, no mastoid tenderness",
            "temperature 38.2, no neck stiffness, throat mildly injected",
        ),
        impressions=(
            "Acute otitis media of the right ear without complication",
            "Acute otitis media with spontaneous perforation and resolving pain",
        ),
        plans=(
            "Analgesia and a delayed antibiotic prescription with clear escalation advice",
            "Review if fever persists beyond seventy-two hours or discharge continues",
        ),
        imaging_findings=("Mastoid air cells clear. No intracranial extension.",),
        lab_findings=(
            "Inflammatory markers mildly raised; ear swab grew mixed respiratory flora",
        ),
    ),
    Condition(
        key="ankle_sprain",
        label="Lateral ankle sprain",
        specialty="Orthopaedics",
        lay_symptoms=(
            "rolled my ankle playing football, swollen on the outside and painful to weight-bear",
            "twisted the ankle stepping off a kerb, bruised and puffy on the outer side",
        ),
        clinical_symptoms=(
            "inversion injury with lateral ligament tenderness and preserved ability to weight-bear",
            "soft tissue injury of the lateral ligament complex without bony tenderness",
        ),
        exam_findings=(
            "tenderness over the anterior talofibular ligament, no tenderness over either malleolus",
            "able to weight-bear four steps, anterior drawer test negative",
        ),
        impressions=(
            "Grade II lateral ankle sprain; Ottawa rules do not indicate radiography",
            "Lateral ligament sprain with functional instability",
        ),
        plans=(
            "Relative rest, ice, compression, and early mobilisation with a graded return to sport",
            "Physiotherapy referral for proprioceptive rehabilitation if symptoms persist at six weeks",
        ),
        imaging_findings=(
            "No fracture. Soft tissue swelling lateral to the ankle joint.",
        ),
        lab_findings=("No laboratory investigation indicated for this presentation",),
        distractor_keys=("gout",),
    ),
    Condition(
        key="hypercholesterolaemia",
        label="Hypercholesterolaemia",
        specialty="Primary Care",
        lay_symptoms=(
            "no symptoms at all, cholesterol flagged on a workplace screening test",
            "feeling well, attending to discuss a raised cholesterol result",
        ),
        clinical_symptoms=(
            "elevated low-density lipoprotein cholesterol on a fasting lipid profile without symptoms",
            "dyslipidaemia identified on cardiovascular risk screening",
        ),
        exam_findings=(
            "no tendon xanthomata, no corneal arcus, BMI 27.6",
            "blood pressure 128/78, peripheral pulses present and symmetrical",
        ),
        impressions=(
            "Primary hypercholesterolaemia with a ten-year cardiovascular risk of 12 percent",
            "Dyslipidaemia warranting lipid-lowering therapy after shared decision making",
        ),
        plans=(
            "Commence a moderate-intensity statin; repeat lipids and liver function at three months",
            "Dietary review and structured physical activity advice provided",
        ),
        imaging_findings=("Coronary calcium not quantified on this study.",),
        lab_findings=(
            "Total cholesterol 7.2 mmol/L, LDL 4.9 mmol/L, HDL 1.1 mmol/L, triglycerides 1.8 mmol/L",
        ),
        distractor_keys=("hypertension",),
    ),
    Condition(
        key="viral_gastroenteritis",
        label="Viral gastroenteritis",
        specialty="Primary Care",
        lay_symptoms=(
            "watery diarrhoea and vomiting since yesterday with stomach cramps and no appetite",
            "sudden sickness and loose stools after a family gathering, feeling drained",
        ),
        clinical_symptoms=(
            "acute onset watery diarrhoea with vomiting and diffuse abdominal cramping",
            "self-limiting gastrointestinal illness with a clear point-source exposure history",
        ),
        exam_findings=(
            "mildly dry mucous membranes, abdomen soft with generalised discomfort, no guarding",
            "no fever, no blood in the stool, observations otherwise stable",
        ),
        impressions=(
            "Viral gastroenteritis with mild dehydration",
            "Self-limiting infective gastroenteritis; no features suggesting invasive infection",
        ),
        plans=(
            "Oral rehydration advice with clear escalation criteria; avoid antimotility agents",
            "Exclusion from work for forty-eight hours after symptoms settle",
        ),
        imaging_findings=(
            "No obstruction or free air. Non-specific bowel gas pattern.",
        ),
        lab_findings=(
            "Electrolytes mildly deranged with a normal white cell count; stool culture negative",
        ),
    ),
)

CONDITIONS = CONDITIONS + FILLER_ONLY_CONDITIONS

CONDITIONS_BY_KEY: dict[str, Condition] = {
    condition.key: condition for condition in CONDITIONS
}
