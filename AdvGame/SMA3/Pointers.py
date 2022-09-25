"""SMA3 Pointers
Locations of in-game data pointers. The vanilla location is commented."""

### Movable pointers, so that the code can still find the data if it's been
###  moved to another location

sublevelmainptrs = 0x0802C9D8   # 081EF1A4 pointer table
sublevelspriteptrs = 0x0802C9E0 # 081EF57C pointer table
objlengthprop = 0x0801735C      # 081C19D8
headerbitcounts = 0x08017244    # 08167766

entrancemainptrs = (0x0802C7A8, 0x08006118) # 081EF08C pointer table
entrancemidwayptrs = 0x08002FE8             # 081643BC pointer table
entrancemainptrsvanilla = 0x081EF08C
entrancemidwayptrsvanilla = 0x081643BC

tilemapL1_8x8 = 0x081BAD20   # pointer table

levelgfxlayerglobal = (
    # pointer, VRAM offset, size
    (0x0824ACC8, 0x1000, -1),   # 0824A070
    (0x08013798, 0x4400, 0x400), # 0827E47C
    (0x08013534, 0x4A00, -1),   # 0824C2BC
    )
levelgfxL1 = 0x08165C44         # pointer table
levelgfxL1W6 = 0x08165D04       # pointer table
levelgfxL2 = 0x08165DC4         # pointer table
levelgfxL3 = 0x08165EC4         # pointer table
leveltilemapL23 = {2:0x081675E4, 3:0x0816766C}   # pointer table
levelgfxspriteglobal = (
    (0x0802C9EC, 0, -1),        # 082AF690, also referenced at many locations
    (0x0802C9F4, 0x4000, -1),   # 082C6CF8
    )
levelgfxstripeIDs = 0x080137A4  # 08166044
levelgfxstripe = 0x080137B0     # 081663C8
levelgfxstripesbyID = {
    0x1A:0x082B7FC0, 0x1B:0x082B7FC4, 0x1C:0x082B7FC8, 0x1D:0x082B7FCC,
    0x1E:0x082B7FD0, 0x1F:0x082B7FD4, 0x20:0x082B7FD8, 0x21:0x082B7FDC,
    0x22:0x082B7FE0, 0x23:0x082B7FE4, 0x24:0x082B7FE8, 0x25:0x082B7FEC,
    0x26:0x082B7FF0, 0x27:0x082B7FF4, 0x28:0x082B7FF8, 0x29:0x082B7FFC,
    0x2A:0x082B8000, 0x2B:0x082B8004, 0x2C:0x082B8008, 0x2D:0x082B800C,
    0x2E:0x082B8010, 0x2F:0x082B8014, 0x30:0x082B8018, 0x31:0x082B801C,
    0x32:0x082B8020, 0x33:0x082B8024, 0x34:0x082B8028, 0x35:0x082B802C,
    0x36:0x082B8030, 0x37:0x082B8034, 0x38:0x082B8038, 0x39:0x082B803C,
    0x3A:0x082BD2A8, 0x3B:0x082BD2AC, 0x3C:0x082BD2B0, 0x3D:0x082BD2B4,
    0x3E:0x082BD2B8, 0x3F:0x082BD2BC, 0x40:0x082BD2C0, 0x41:0x082BD2C4,
    0x42:0x082BD2C8, 0x43:0x082BD2CC, 0x44:0x082BD2D0, 0x45:0x082BD2D4,
    0x46:0x082BD2D8, 0x47:0x082BD2DC, 0x48:0x082BD2E0, 0x49:0x082BD2E4,
    0x4A:0x082BD2E8, 0x4B:0x082BD2EC, 0x4C:0x082BD2F0, 0x4D:0x082BD2F4,
    0x4E:0x082BD2F8, 0x4F:0x082BD2FC, 0x50:0x082BD300, 0x51:0x082BD304,
    0x52:0x082BD308, 0x53:0x082BD30C, 0x54:0x082BD310, 0x55:0x082BD314,
    0x56:0x082BD318, 0x57:0x082BD31C, 0x58:0x082BD320, 0x59:0x082BD324,
    0x5A:0x082C2500, 0x5B:0x082C2504, 0x5C:0x082C2508, 0x5D:0x082C250C,
    0x5E:0x082C2510, 0x5F:0x082C2514, 0x60:0x082C2518, 0x61:0x082C251C,
    0x62:0x082C2520, 0x63:0x082C2524, 0x64:0x082C2528, 0x65:0x082C252C,
    0x66:0x082C2530, 0x67:0x082C2534, 0x68:0x082C2538, 0x69:0x082C253C,
    0x6A:0x082C24E0, 0x6B:0x082C24E4, 0x6C:0x082C24E8, 0x6D:0x082C24EC,
    0x6E:0x082C24F0, 0x6F:0x082C24F4, 0x70:0x082C24F8, 0x71:0x082C24FC,
    0xA9:0x082C2540, 0xAA:0x082C2544, 0xAB:0x082C2548, 0xAC:0x082C254C,
    0xAD:0x082C2550, 0xAE:0x082C2554, 0xAF:0x082C2558, 0xB0:0x082C255C,
    }
levelgfxanimglobal = (
    (0x0827F87C, 0x4800, 0x80),
    (0x0827F97C, 0x4880, 0x80),
    (0x0827FD7C, 0x4900, 0x80),
    (0x0828C2FC, 0x4980, 0x80),
    )
levelgfxAnimIDs = {
    0x01:(
        (0x0827987C, 0x8C00, 0x400),
        ),
    0x02:(
        (0x0828087C, 0x4000, 0x100),
        (0x0828107C, 0x4100, 0x100),
        (0x0828097C, 0x4200, 0x100),
        (0x0828117C, 0x4300, 0x100),
        (0x0827F87C, 0x4400, 0x100), #\
        (0x0827F87C, 0x4500, 0x100), #| irrelevant, but the game copies them
        (0x0827F97C, 0x4600, 0x100), #|
        (0x0827F97C, 0x4700, 0x100), #/
        ),
    0x03:(
        (0x0828387C, 0x8C00, 0x400),
        ),
    0x05:(
        (0x0828487C, 0x8C00, 0x400),
        ),
    (0x06,0x0A):(
        (0x0828487C, 0x1E00, 0x400),
        ),
    0x07:(
        (0x0828007C, 0x4000, 0x100),
        (0x0828017C, 0x4200, 0x100),
        (0x0828247C, 0x4100, 0x100),
        (0x0828257C, 0x4300, 0x100),
        ),
    (0x07,0x0A):(
        (0x0827A87C, 0x4000, 0x100),
        (0x0827A97C, 0x4200, 0x100),
        (0x0827B07C, 0x4100, 0x100),
        (0x0827B17C, 0x4300, 0x100),
        ),
    0x08:(
        (0x08281C7C, 0x4000, 0x100),
        (0x08281D7C, 0x4200, 0x100),
        ),
    0x0A:(
        (0x0828787C, 0x8C00, 0x400),
        ),
    0x0C:(
        (0x0828187C, 0x4000, 0x200),
        (0x0828197C, 0x4200, 0x200),
        (0x0828307C, 0x4100, 0x200),
        (0x0828317C, 0x4300, 0x200),
        ),
    0x0F:(
        (0x0828687C, 0x8C00, 0x400),
        ),
    0x10:(
        (0x0828987C, 0x8C00, 0x200),
        ),
    }
levelgfxAnim09 = 0x08016D14     # 08207E3C
levelgfxAnim12 = 0x08016D0C     # 0828F87C

levelpalL1 = 0x08013988         # 08167284, also referenced at 0x080D69E0
levelpalL2 = 0x0801389C         # 08167304
levelpalL3 = 0x080138A0         # 08167384
levelpalL3image = 0x08013A88    # 08167434
levelBGgradient = 0x0802F170    # 0816961C
levelpal100 = 0x08013C84        # 082D285C   also referenced at 0x080E58EC
levelpal180 = 0x08013C90        # 082D311C   also referenced at 0x080142F0,0x080E58F8
levelpal1F8 = 0x080E97D0        # 08195A00
levelpalsprite = 0x08013CB4     # 08167454   also referenced at 0x08014310
levelpalyoshi = 0x082D301C      # This is a direct color table, not a pointer
    # Actually more movable if loaded this way, than using the in-game lookup?
levelpalunusedDE = 0x080138A4   # 08167404   also referenced in various locations

textstandardmsg = 0x080E93CC    # 082F5E18   also referenced at 0x0810CA04
textlevelnames = 0x080FCDC4     # 082F9888
text68ending = 0x08106E6C       # 082F5D11
textfileselect = 0x080FF134     # 081995E0   also referenced in various other locations
textstoryintro = 0x08033070     # 0816B748   also referenced at 0x08033218
textcredits = 0x080343E4        # 0816DB0C
# Last 3 pointers of textcredits are hardcoded (0816D3F6, 0816D446, 0816D46E)
textcreditsfinal = (0x08034910, 0x0803502C, 0x08035160)

### Not fixed-size data, but too many references to practically move
colortable = 0x082CF008


# Compressed data export file names, and all references to each file's pointer.
# Allows extracting and reinserting at a different location.
LZ77_graphics = [
    # 4bpp graphics
    ("LZ77_SMA3Title_buildtext.bin", (0x08003918,)),    # 081644D4
    ("LZ77_YITitle_sprite.bin", (0x080FE564,)),         # 0819A890
    ("LZ77_YITitle_L3_W15.bin", (0x08199110,)),         # 0819DABC
    ("LZ77_YITitle_L3_W6.bin", (0x08199114,)),          # 0819E1E0
    ("LZ77_YITitle_L1.bin", (0x080FE928,)),             # 0819E984
    ("LZ77_YITitle_L0.bin", (0x080FE930,)),             # 081A42D8
    ("LZ77_Gameplay_Froggy.bin", (0x080C5734,)),        # 081A8034
    ("LZ77_LevelSelect_icon24.bin", (0x0800F380, 0x08010ED0)), # 081EF954
    ("LZ77_LevelSelect_icon32_0.bin", (                 # 081F3398
        0x08008404, 0x08008FF4, 0x080092BC, 0x0800BBDC, 0x0800BF2C, 0x0800C40C,
        0x0800C878, 0x0800D3C8, 0x0800DCA0, 0x0800E528, 0x0800EB84, 0x0801315C,
        0x080132AC)),
    ("LZ77_LevelSelect_icon32_1.bin", (                 # 081F7174
        0x0800840C, 0x08008F84, 0x0800BB70, 0x0800BF8C, 0x0800D464, 0x0800DD28,
        0x0800EBFC, 0x0801129C, 0x080130F0, 0x08013348)),
    ("LZ77_LevelSelect_controls.bin", (   # also includes story intro
        0x08008174, 0x08030FF4)),                       # 081F7A90
    ("LZ77_LevelSelect_stripe00.bin", (0x081FE384,)),   # 081FE17C
    ("LZ77_LevelSelect_stripe08.bin", (0x081FE388,)),   # 081FE2B0
    ("LZ77_LevelSelect_Perfect.bin", (0x0800D910,)),    # 081FE38C
    ("LZ77_LevelSelect_400.bin", (0x08008180,)),        # 081FE754
    ("LZ77_WorldSelect_L12_0.bin", (0x082010E4,)),      # 081FF38C
    ("LZ77_WorldSelect_L12_1.bin", (0x082010E8,)),      # 081FFF20
    ("LZ77_WorldSelect_L12_2.bin", (0x082010EC,)),      # 08200B70
    ("LZ77_WorldSelect_stripe02.bin", (0x082016AC,)),   # 082010F0
    ("LZ77_WorldSelect_stripe0A.bin", (0x082016B0,)),   # 08201334
    ("LZ77_WorldSelect_BabyLuigi.bin", (0x082016B4,)),  # 08201550
    ("LZ77_ScoreCalc_sprite.bin", (0x080E58DC,)),       # 08207980
    ("LZ77_Gameplay_anim_12.bin", (0x08016D0C,)),       # 08207E3C
    ("LZ77_Unused082097E4.bin", (0x0820C1B4,)),         # 082097E4
    ("LZ77_Unused08209CC4.bin", (0x0820C1B8,)),         # 08209CC4
    ("LZ77_Unused0820A638.bin", (0x0820C1BC,)),         # 0820A638
    ("LZ77_Unused0820B0BC.bin", (0x0820C1C0,)),         # 0820B0BC
    ("LZ77_Unused0820BA04.bin", (0x0820C1C4,)),         # 0820BA04
    ("LZ77_Unused0820BBF0.bin", (0x0820C1C8,)),         # 0820BBF0
    ("LZ77_Unused0820BDDC.bin", (0x0820C1CC,)),         # 0820BDDC
    ("LZ77_Unused0820BFC8.bin", (0x0820C1D0,)),         # 0820BFC8
    ("LZ77_100Cutscene_sprite_0.bin", (0x080F6EA8, 0x080F6F44)), # 0820E290
    ("LZ77_100Cutscene_sprite_1.bin", (0x080F6F08, 0x080F7004)), # 0820F13C
    ("LZ77_100Cutscene_layer.bin", (0x080F6E5C,)),      # 0820FFB8
    ("LZ77_100Cutscene_text.bin", (0x080F6E60,)),       # 08214EC4
    ("LZ77_100Cutscene_end.bin", (0x080F7E24,)),        # 08215308
    ("LZ77_BanditMinigame_2.bin", (0x08165B2C, 0x082272C0)), # 082255CC
    ("LZ77_BanditMinigame_3.bin", (0x082272C4,)),       # 08225ED0
    ("LZ77_IntroCutscene_L1.bin", (0x082272C8,)),       # 08226908
    ("LZ77_Gameplay_L1_200.bin", (0x0822C8E0,)),        # 08227C90
    ("LZ77_Gameplay_L1_300.bin", (0x0822C8E4,)),        # 0822874C
    ("LZ77_Gameplay_L1_201.bin", (0x0822C8E8,)),        # 082291C4
    ("LZ77_Gameplay_L1_301.bin", (0x0822C8EC,)),        # 08229C0C
    ("LZ77_Gameplay_L1_204.bin", (0x0822C8F0,)),        # 0822A5D4
    ("LZ77_Gameplay_L1_304.bin", (0x0822C8F4,)),        # 0822AD94
    ("LZ77_Gameplay_L1_205.bin", (0x0822C8F8,)),        # 0822B4EC
    ("LZ77_Gameplay_L1_305.bin", (0x0822C8FC,)),        # 0822BEDC
    ("LZ77_Gameplay_L1_202.bin", (0x082315D4,)),        # 0822C900
    ("LZ77_Gameplay_L1_302.bin", (0x082315D8,)),        # 0822D394
    ("LZ77_Gameplay_L1_203.bin", (0x082315DC,)),        # 0822DC68
    ("LZ77_Gameplay_L1_303.bin", (0x082315E0,)),        # 0822E578
    ("LZ77_Gameplay_L1_206.bin", (0x082315E4,)),        # 0822EBEC
    ("LZ77_Gameplay_L1_306.bin", (0x082315E8,)),        # 0822F6B4
    ("LZ77_Gameplay_L1_207.bin", (0x082315EC,)),        # 08230294
    ("LZ77_Gameplay_L1_307.bin", (0x082315F0,)),        # 08230CC8
    ("LZ77_Gameplay_L1_208.bin", (0x08236630,)),        # 082315F4
    ("LZ77_Gameplay_L1_308.bin", (0x08236634,)),        # 0823213C
    ("LZ77_Gameplay_L1_209.bin", (0x08236638,)),        # 08232C80
    ("LZ77_Gameplay_L1_309.bin", (0x0823663C,)),        # 0823362C
    ("LZ77_Gameplay_L1_20C.bin", (0x08236640,)),        # 08234278
    ("LZ77_Gameplay_L1_30C.bin", (0x08236644,)),        # 08234EB0
    ("LZ77_Gameplay_L1_20D.bin", (0x08236648,)),        # 082355A0
    ("LZ77_Gameplay_L1_30D.bin", (0x0823664C,)),        # 08235EDC
    ("LZ77_Gameplay_L1_20A.bin", (0x0823BC34,)),        # 08236650
    ("LZ77_Gameplay_L1_30A.bin", (0x0823BC38,)),        # 08237050
    ("LZ77_Gameplay_L1_20B.bin", (0x0823BC3C,)),        # 08237AE0
    ("LZ77_Gameplay_L1_30B.bin", (0x0823BC40,)),        # 0823869C
    ("LZ77_Gameplay_L1_20E.bin", (0x0823BC44,)),        # 08239234
    ("LZ77_Gameplay_L1_30E.bin", (0x0823BC48,)),        # 08239E70
    ("LZ77_Gameplay_L1_20F.bin", (0x0823BC4C,)),        # 0823A8A8
    ("LZ77_Gameplay_L1_30F.bin", (0x0823BC50,)),        # 0823B1B8
    ("LZ77_Gameplay_L1_000.bin", (0x08240B24,)),        # 0823BC54
    ("LZ77_Gameplay_L1_001.bin", (0x08240B28,)),        # 0823C774
    ("LZ77_Gameplay_L1_004.bin", (0x08240B2C,)),        # 0823D378
    ("LZ77_Gameplay_L1_005.bin", (0x08240B30,)),        # 0823DD3C
    ("LZ77_Gameplay_L1_002.bin", (0x08240B34,)),        # 0823E734
    ("LZ77_Gameplay_L1_003.bin", (0x08240B38,)),        # 0823EC78
    ("LZ77_Gameplay_L1_006.bin", (0x08240B3C,)),        # 0823F4C8
    ("LZ77_Gameplay_L1_007.bin", (0x08240B40,)),        # 0823FFAC
    ("LZ77_IntroCutscene_L2_5.bin", (0x08245CB0,)),     # 08240B44
    ("LZ77_IntroCutscene_L2_6.bin", (0x08245CB4,)),     # 082414A0
    ("LZ77_Credits_L0.bin", (0x08165B98, 0x08245CB8)),  # 08241C9C
    ("LZ77_Gameplay_L1_211.bin", (0x08245CBC,)),        # 082423BC
    ("LZ77_Gameplay_L1_311.bin", (0x08245CC0,)),        # 0824300C
    ("LZ77_Gameplay_L1_011.bin", (0x08245CC4,)),        # 08243CA4
    ("LZ77_Credits_201.bin", (0x08245CC8,)),            # 082448F0
    ("LZ77_Unused08245430.bin", (0x08245CCC,)),         # 08245430
    ("LZ77_GoalMinigame_2.bin", (                       # 08245CD0
        0x080EFD38, 0x080F2CF4, 0x080F439C)),
    ("LZ77_GoalMinigame_0.bin", (0x0824ACB0,)),         # 08246EB8
    ("LZ77_GoalMinigame_1.bin", (0x0824ACB4,)),         # 08247760
    ("LZ77_GoalMinigame_4.bin", (0x0824ACB8,)),         # 08247D90
    ("LZ77_GoalMinigame_5.bin", (0x0824ACBC,)),         # 082485D4
    ("LZ77_Gameplay_L2_500.bin", (0x0824ACC0,)),        # 08248E48
    ("LZ77_Gameplay_L2_600.bin", (0x0824ACC4,)),        # 08249700
    ("LZ77_Gameplay_L1_100.bin", (0x0824ACC8,)),        # 0824A070
    ("LZ77_Unused0824AABC.bin", (0x0824ACCC,)),         # 0824AABC
    ("LZ77_Gameplay_L1_4A0.bin", (0x08013534,)),        # 0824C2BC
    ("LZ77_Gameplay_L2_503.bin", (0x08251260,)),        # 0824C578
    ("LZ77_Gameplay_L2_603.bin", (0x08251264,)),        # 0824CF0C
    ("LZ77_Gameplay_L2_502.bin", (0x08251268,)),        # 0824D6E8
    ("LZ77_Gameplay_L2_602.bin", (0x0825126C,)),        # 0824E2D8
    ("LZ77_Gameplay_L2_50B.bin", (0x08251270,)),        # 0824EEAC
    ("LZ77_Gameplay_L2_611.bin", (0x08251274,)),        # 0824F700
    ("LZ77_Gameplay_L2_508.bin", (0x08251278,)),        # 0824FF94
    ("LZ77_Gameplay_L2_608.bin", (0x0825127C,)),        # 082507DC
    ("LZ77_Gameplay_L2_501.bin", (0x08255F58,)),        # 08251280
    ("LZ77_Gameplay_L2_51C.bin", (0x08255F5C,)),        # 08251B50
    ("LZ77_Gameplay_L2_507.bin", (0x08255F60,)),        # 082524D8
    ("LZ77_Gameplay_L2_607.bin", (0x08255F64,)),        # 0825320C
    ("LZ77_Gameplay_L2_506.bin", (0x08255F68,)),        # 08253A9C
    ("LZ77_Gameplay_L2_518.bin", (0x08255F6C,)),        # 082544B4
    ("LZ77_Gameplay_L2_519.bin", (0x08255F70,)),        # 08254CFC
    ("LZ77_Unused0825573C.bin", (0x08255F74,)),         # 0825573C
    ("LZ77_Gameplay_L2_505.bin", (0x0825A844,)),        # 08255F78
    ("LZ77_Gameplay_L2_609.bin", (0x0825A848,)),        # 0825665C
    ("LZ77_Gameplay_L2_50A.bin", (0x0825A84C,)),        # 082571B0
    ("LZ77_Gameplay_L2_51E.bin", (0x0825A850,)),        # 08257C30
    ("LZ77_Gameplay_L2_50C.bin", (0x0825A854,)),        # 08258688
    ("LZ77_Gameplay_L2_60C.bin", (0x0825A858,)),        # 0825913C
    ("LZ77_Gameplay_L2_50D.bin", (0x0825A85C,)),        # 08259D80
    ("LZ77_Gameplay_L2_605.bin", (0x0825A860,)),        # 0825A250
    ("LZ77_Gameplay_L2_50E.bin", (0x0825FA20,)),        # 0825A864
    ("LZ77_Gameplay_L2_514.bin", (0x0825FA24,)),        # 0825B3A4
    ("LZ77_Gameplay_L2_50F.bin", (0x0825FA28,)),        # 0825C070
    ("LZ77_Gameplay_L2_60F.bin", (0x0825FA2C,)),        # 0825CA18
    ("LZ77_Gameplay_L2_513.bin", (0x0825FA30,)),        # 0825D3B0
    ("LZ77_Gameplay_L2_613.bin", (0x0825FA34,)),        # 0825DC50
    ("LZ77_Gameplay_L2_515.bin", (0x0825FA38,)),        # 0825E690
    ("LZ77_Gameplay_L2_615.bin", (0x0825FA3C,)),        # 0825F038
    ("LZ77_LevelSelect_Yoshi.bin", (0x0826443C,)),      # 0825FA40
    ("LZ77_Credits_200.bin", (0x08165BA4, 0x08264440)), # 082601E4
    ("LZ77_Credits_300.bin", (0x08165BB0, 0x08264444)), # 08260FB4
    ("LZ77_WorldSelect_stripe00.bin", (0x08264448,)),   # 08261938
    ("LZ77_Gameplay_L2_606.bin", (0x0826444C,)),        # 08261DAC
    ("LZ77_Gameplay_Bowser_stripe22.bin", (0x08264450,)), # 08262668
    ("LZ77_Gameplay_Bowser_L1.bin", (0x08264454,)),     # 08262F94
    ("LZ77_Gameplay_Bowser_stripe02.bin", (0x08264458,)), # 08263AB4
    ("LZ77_Gameplay_L2_516.bin", (0x082686EC,)),        # 0826445C
    ("LZ77_Gameplay_L2_616.bin", (0x082686F0,)),        # 08264B68
    ("LZ77_Gameplay_L2_601.bin", (0x082686F4,)),        # 082650D8
    ("LZ77_Gameplay_L2_60D.bin", (0x082686F8,)),        # 08265808
    ("LZ77_Gameplay_L2_51D.bin", (0x082686FC,)),        # 082660C0
    ("LZ77_Gameplay_L2_61D.bin", (0x08268700,)),        # 08266A10
    ("LZ77_Gameplay_L2_51F.bin", (0x08268704,)),        # 082672D0
    ("LZ77_Gameplay_L2_61F.bin", (0x08268708,)),        # 08267CB8
    ("LZ77_Gameplay_L3_70D.bin", (0x0826ABC4,)),        # 0826870C
    ("LZ77_Gameplay_L3_80C.bin", (0x0826ABC8,)),        # 08268C3C
    ("LZ77_Gameplay_L3_70A.bin", (0x0826ABCC,)),        # 0826922C
    ("LZ77_Gameplay_L3_709.bin", (0x0826ABD0,)),        # 082695CC
    ("LZ77_Gameplay_L3_701.bin", (0x0826ABD4,)),        # 0826982C
    ("LZ77_Gameplay_L3_712.bin", (0x0826ABD8,)),        # 08269E98
    ("LZ77_Gameplay_L3_702.bin", (0x0826ABDC,)),        # 0826A200
    ("LZ77_Gameplay_L3_812.bin", (0x0826ABE0,)),        # 0826A59C
    ("LZ77_Gameplay_L3_703.bin", (0x0826DC64,)),        # 0826ABE4
    ("LZ77_Gameplay_L3_71E.bin", (0x0826DC68,)),        # 0826B328
    ("LZ77_Gameplay_L3_70C.bin", (0x0826DC6C,)),        # 0826B994
    ("LZ77_Gameplay_L3_718.bin", (0x0826DC70,)),        # 0826BD60
    ("LZ77_GoalMinigame_7.bin", (0x0826DC74,)),         # 0826C380
    ("LZ77_GoalMinigame_8.bin", (0x0826DC78,)),         # 0826CBA4
    ("LZ77_Gameplay_KamekRoom.bin", (0x0826DC7C,)),     # 0826D1A4
    ("LZ77_Unused0826D854.bin", (0x0826DC80,)),         # 0826D854
    ("LZ77_ScoreCalc_L3anim_0.bin", (0x08270C38,)),     # 0826DC84
    ("LZ77_ScoreCalc_L3anim_1.bin", (0x08270C3C,)),     # 0826E1C4
    ("LZ77_ScoreCalc_L3anim_2.bin", (0x08270C40,)),     # 0826E734
    ("LZ77_StoryIntro_L2.bin", (0x08165B50, 0x08270C44)), # 0826ECA0
    ("LZ77_Gameplay_L3_70E.bin", (0x08270C48,)),        # 0826F1BC
    ("LZ77_Gameplay_L3_80E.bin", (0x08270C4C,)),        # 0826F84C
    ("LZ77_Gameplay_L3_70F.bin", (0x08270C50,)),        # 0826FF24
    ("LZ77_Gameplay_L3_80F.bin", (0x08270C54,)),        # 0827070C
    ("LZ77_Gameplay_L3_700.bin", (0x082741EC,)),        # 08270C58
    ("LZ77_Gameplay_L3_713.bin", (0x082741F0,)),        # 082712F8
    ("LZ77_082718B8.bin", (0x082741F4,)),               # 082718B8
    ("LZ77_BanditMinigame_7.bin", (0x082741F8,)),       # 08271EEC
    ("LZ77_Gameplay_L3_704.bin", (0x082741FC,)),        # 082725DC
    ("LZ77_Gameplay_L3_804.bin", (0x08274200,)),        # 08272CDC
    ("LZ77_Gameplay_L3_715.bin", (0x08274204,)),        # 08273350
    ("LZ77_Gameplay_L3_717.bin", (0x08274208,)),        # 0827380C
    ("LZ77_Unused0827420C.bin", (0x08276C30,)),         # 0827420C
    ("LZ77_WorldSelect_L3_8.bin", (0x08276C34,)),       # 082747D8
    ("LZ77_Gameplay_L3_729.bin", (0x08276C38,)),        # 08274DBC
    ("LZ77_Gameplay_L3_829.bin", (0x08276C3C,)),        # 08275540
    ("LZ77_Gameplay_L3_72F.bin", (0x08276C40,)),        # 08275B74
    ("LZ77_Unused082760C8.bin", (0x08276C44,)),         # 082760C8
    ("LZ77_Gameplay_L3_716.bin", (0x08276C48,)),        # 082762E4
    ("LZ77_Gameplay_L3_816.bin", (0x08276C4C,)),        # 08276764
    ("LZ77_Gameplay_L3_720.bin", (0x0827985C,)),        # 08276C50
    ("LZ77_Gameplay_L3_722.bin", (0x08279860,)),        # 08277254
    ("LZ77_Gameplay_L3_811.bin", (0x08279864,)),        # 082776BC
    ("LZ77_Gameplay_L3_724.bin", (0x08279868,)),        # 08277BB8
    ("LZ77_Gameplay_L3_725.bin", (0x0827986C,)),        # 0827834C
    ("LZ77_Gameplay_L3_726.bin", (0x08279870,)),        # 0827893C
    ("LZ77_Gameplay_L3_727.bin", (0x08279874,)),        # 08278C58
    ("LZ77_Gameplay_L3_72C.bin", (0x08279878,)),        # 08279214
    ("LZ77_Gameplay_anim_09.bin", (0x08016D14,)),       # 0828F87C
    ("LZ77_StoryIntro_sprite_00.bin", (0x08165B44,)),   # 082AAEA4
    ("LZ77_StoryIntro_sprite_01.bin", (0x08031258, 0x080317A4)), # 082AE310
    ("LZ77_Gameplay_sprite_1000.bin", (                 # 082AF690
        0x080046F0, 0x08008154, 0x0802C9EC, 0x080EA7A0, 0x080EAAAC, 0x080EFD44,
        0x080F60B4, 0x080F736C, 0x080FE56C)),
    ("LZ77_Gameplay_PauseMenu.bin", (                   # 082B2480
        0x080FB998, 0x0810D7B0, 0x0810E7C4)),
    ("LZ77_Gameplay_stripe_1A.bin", (0x082B7FC0,)),     # 082B2C8C
    ("LZ77_Gameplay_stripe_1B.bin", (0x082B7FC4,)),     # 082B2FAC
    ("LZ77_Gameplay_stripe_1C.bin", (0x082B7FC8,)),     # 082B3194
    ("LZ77_Gameplay_stripe_1D.bin", (0x082B7FCC,)),     # 082B3394
    ("LZ77_Gameplay_stripe_1E.bin", (0x082B7FD0,)),     # 082B3614
    ("LZ77_Gameplay_stripe_1F.bin", (0x082B7FD4,)),     # 082B3924
    ("LZ77_Gameplay_stripe_20.bin", (0x082B7FD8,)),     # 082B3BF0
    ("LZ77_Gameplay_stripe_21.bin", (0x082B7FDC,)),     # 082B3F44
    ("LZ77_Gameplay_stripe_22.bin", (0x082B7FE0,)),     # 082B4218
    ("LZ77_Gameplay_stripe_23.bin", (0x082B7FE4,)),     # 082B44C0
    ("LZ77_Gameplay_stripe_24.bin", (0x082B7FE8,)),     # 082B470C
    ("LZ77_Gameplay_stripe_25.bin", (0x082B7FEC,)),     # 082B4980
    ("LZ77_Gameplay_stripe_26.bin", (0x082B7FF0,)),     # 082B4C44
    ("LZ77_Gameplay_stripe_27.bin", (0x082B7FF4,)),     # 082B4F5C
    ("LZ77_Gameplay_stripe_28.bin", (0x082B7FF8,)),     # 082B5200
    ("LZ77_Gameplay_stripe_29.bin", (0x082B7FFC,)),     # 082B5480
    ("LZ77_Gameplay_stripe_2A.bin", (0x082B8000,)),     # 082B5768
    ("LZ77_Gameplay_stripe_2B.bin", (0x082B8004,)),     # 082B5928
    ("LZ77_Gameplay_stripe_2C.bin", (0x082B8008,)),     # 082B5B88
    ("LZ77_Gameplay_stripe_2D.bin", (0x082B800C,)),     # 082B5DF0
    ("LZ77_Gameplay_stripe_2E.bin", (0x082B8010,)),     # 082B60AC
    ("LZ77_Gameplay_stripe_2F.bin", (0x082B8014,)),     # 082B62C0
    ("LZ77_Gameplay_stripe_30.bin", (0x082B8018,)),     # 082B6538
    ("LZ77_Gameplay_stripe_31.bin", (0x082B801C,)),     # 082B6750
    ("LZ77_Gameplay_stripe_32.bin", (0x082B8020,)),     # 082B697C
    ("LZ77_Gameplay_stripe_33.bin", (0x082B8024,)),     # 082B6C1C
    ("LZ77_Gameplay_stripe_34.bin", (0x082B8028,)),     # 082B6ED4
    ("LZ77_Gameplay_stripe_35.bin", (0x082B802C,)),     # 082B71C0
    ("LZ77_Gameplay_stripe_36.bin", (0x082B8030,)),     # 082B74E0
    ("LZ77_Gameplay_stripe_37.bin", (0x082B8034,)),     # 082B77E0
    ("LZ77_Gameplay_stripe_38.bin", (0x082B8038,)),     # 082B79E0
    ("LZ77_Gameplay_stripe_39.bin", (0x082B803C,)),     # 082B7C80
    ("LZ77_Gameplay_stripe_3A.bin", (0x082BD2A8,)),     # 082B8040
    ("LZ77_Gameplay_stripe_3B.bin", (0x082BD2AC,)),     # 082B82F0
    ("LZ77_Gameplay_stripe_3C.bin", (0x082BD2B0,)),     # 082B8620
    ("LZ77_Gameplay_stripe_3D.bin", (0x082BD2B4,)),     # 082B88FC
    ("LZ77_Gameplay_stripe_3E.bin", (0x082BD2B8,)),     # 082B8BB4
    ("LZ77_Gameplay_stripe_3F.bin", (0x082BD2BC,)),     # 082B8E98
    ("LZ77_Gameplay_stripe_40.bin", (0x082BD2C0,)),     # 082B9130
    ("LZ77_Gameplay_stripe_41.bin", (0x082BD2C4,)),     # 082B939C
    ("LZ77_Gameplay_stripe_42.bin", (0x082BD2C8,)),     # 082B95BC
    ("LZ77_Gameplay_stripe_43.bin", (0x082BD2CC,)),     # 082B97E4
    ("LZ77_Gameplay_stripe_44.bin", (0x082BD2D0,)),     # 082B9A2C
    ("LZ77_Gameplay_stripe_45.bin", (0x082BD2D4,)),     # 082B9D8C
    ("LZ77_Gameplay_stripe_46.bin", (0x082BD2D8,)),     # 082BA008
    ("LZ77_Gameplay_stripe_47.bin", (0x082BD2DC,)),     # 082BA21C
    ("LZ77_Gameplay_stripe_48.bin", (0x082BD2E0,)),     # 082BA500
    ("LZ77_Gameplay_stripe_49.bin", (0x082BD2E4,)),     # 082BA824
    ("LZ77_Gameplay_stripe_4A.bin", (0x082BD2E8,)),     # 082BAAE8
    ("LZ77_Gameplay_stripe_4B.bin", (0x082BD2EC,)),     # 082BAD90
    ("LZ77_Gameplay_stripe_4C.bin", (0x082BD2F0,)),     # 082BB018
    ("LZ77_Gameplay_stripe_4D.bin", (0x082BD2F4,)),     # 082BB340
    ("LZ77_Gameplay_stripe_4E.bin", (0x082BD2F8,)),     # 082BB568
    ("LZ77_Gameplay_stripe_4F.bin", (0x082BD2FC,)),     # 082BB888
    ("LZ77_Gameplay_stripe_50.bin", (0x082BD300,)),     # 082BBB04
    ("LZ77_Gameplay_stripe_51.bin", (0x082BD304,)),     # 082BBD84
    ("LZ77_Gameplay_stripe_52.bin", (0x082BD308,)),     # 082BBFF0
    ("LZ77_Gameplay_stripe_53.bin", (0x082BD30C,)),     # 082BC124
    ("LZ77_Gameplay_stripe_54.bin", (0x082BD310,)),     # 082BC318
    ("LZ77_Gameplay_stripe_55.bin", (0x082BD314,)),     # 082BC5FC
    ("LZ77_Gameplay_stripe_56.bin", (0x082BD318,)),     # 082BC8F0
    ("LZ77_Gameplay_stripe_57.bin", (0x082BD31C,)),     # 082BCBC4
    ("LZ77_Gameplay_stripe_58.bin", (0x082BD320,)),     # 082BCDF0
    ("LZ77_Gameplay_stripe_59.bin", (0x082BD324,)),     # 082BD034
    ("LZ77_Gameplay_stripe_5A.bin", (0x082C2500,)),     # 082BE600
    ("LZ77_Gameplay_stripe_5B.bin", (0x082C2504,)),     # 082BE8A0
    ("LZ77_Gameplay_stripe_5C.bin", (0x082C2508,)),     # 082BEBA0
    ("LZ77_Gameplay_stripe_5D.bin", (0x082C250C,)),     # 082BEE40
    ("LZ77_Gameplay_stripe_5E.bin", (0x082C2510,)),     # 082BF0EC
    ("LZ77_Gameplay_stripe_5F.bin", (0x082C2514,)),     # 082BF3B0
    ("LZ77_Gameplay_stripe_60.bin", (0x082C2518,)),     # 082BF584
    ("LZ77_Gameplay_stripe_61.bin", (0x082C251C,)),     # 082BF7F0
    ("LZ77_Gameplay_stripe_62.bin", (0x082C2520,)),     # 082BFA8C
    ("LZ77_Gameplay_stripe_63.bin", (0x082C2524,)),     # 082BFC88
    ("LZ77_Gameplay_stripe_64.bin", (0x082C2528,)),     # 082BFED8
    ("LZ77_Gameplay_stripe_65.bin", (0x082C252C,)),     # 082C018C
    ("LZ77_Gameplay_stripe_66.bin", (0x082C2530,)),     # 082C0408
    ("LZ77_Gameplay_stripe_67.bin", (0x082C2534,)),     # 082C06D0
    ("LZ77_Gameplay_stripe_68.bin", (0x082C2538,)),     # 082C0970
    ("LZ77_Gameplay_stripe_69.bin", (0x082C253C,)),     # 082C0C20
    ("LZ77_Gameplay_stripe_6A.bin", (0x082C24E0,)),     # 082BD328
    ("LZ77_Gameplay_stripe_6B.bin", (0x082C24E4,)),     # 082BD634
    ("LZ77_Gameplay_stripe_6C.bin", (0x082C24E8,)),     # 082BD8FC
    ("LZ77_Gameplay_stripe_6D.bin", (0x082C24EC,)),     # 082BDB7C
    ("LZ77_Gameplay_stripe_6E.bin", (0x082C24F0,)),     # 082BDD24
    ("LZ77_Gameplay_stripe_6F.bin", (0x082C24F4,)),     # 082BDF68
    ("LZ77_Gameplay_stripe_70.bin", (0x082C24F8,)),     # 082BE164
    ("LZ77_Gameplay_stripe_71.bin", (0x082C24FC,)),     # 082BE40C
    ("LZ77_Gameplay_stripe_A9.bin", (0x082C2540,)),     # 082C0EC8
    ("LZ77_Gameplay_stripe_AA.bin", (0x082C2544,)),     # 082C10E4
    ("LZ77_Gameplay_stripe_AB.bin", (0x082C2548,)),     # 082C12B8
    ("LZ77_Gameplay_stripe_AC.bin", (0x082C254C,)),     # 082C15B4
    ("LZ77_Gameplay_stripe_AD.bin", (0x082C2550,)),     # 082C1910
    ("LZ77_Gameplay_stripe_AE.bin", (0x082C2554,)),     # 082C1B9C
    ("LZ77_Gameplay_stripe_AF.bin", (0x082C2558,)),     # 082C1E74
    ("LZ77_Gameplay_stripe_B0.bin", (0x082C255C,)),     # 082C21C4
    ("LZ77_Gameplay_sprite_1400.bin", (0x0802C9F4,)),   # 082C6CF8
    ("LZ77_StoryIntro_L01.bin", (0x08165B5C,)),         # 082D7FF8
    ("LZ77_ChooseAGame_layer.bin", (0x0810D7A0,)),      # 082DEFBC
    ("LZ77_ChooseAGame_sprite.bin", (0x0810D7A4,)),     # 082E02FC
    ("LZ77_ChooseAGame_sleep.bin", (0x0810D7B8, 0x0810E7CC)), # 082E27D4
    ("LZ77_SMA3Title_L1.bin", (0x08165BEC,)),           # 082E3EE4
    ("LZ77_SMA3Title_sprite.bin", (0x08165BF8,)),       # 082E6870
    ("LZ77_SaveDataCorruption.bin", (0x080FA490,)),     # 082E7740
    ("LZ77_MessageBorder_0.bin", (0x080E9768,)),        # 082F99A8
    ("LZ77_MessageBorder_1.bin", (0x080E9770,)),        # 082F9A6C
    ("LZ77_MessageBorder_2.bin", (0x080E97A0,)),        # 082F9B18
    ("LZ77_MarioBrosTitle_layer.bin", (                 # 08303210
        0x08110D98, 0x08118DAC, 0x08119408, 0x08119BF8)),

    # 8bpp graphics
    ("LZ77_YITitle_L2_8bpp.bin", (0x080FE914,)),        # 08199EA4
    ("LZ77_Gameplay_Bowser_L2_8bpp.bin", (0x08102E40,)), # 081A4A60
    ("LZ77_Gameplay_Raphael_L2_8bpp.bin", (0x08014578,)), # 0820C580
    ("LZ77_Gameplay_Hookbill_L2_8bpp.bin", (0x080CDBE4,)), # 0820DA48
    ("LZ77_Credits_sprite_8bpp.bin", (0x08034368,)),    # 082C2560
    ("LZ77_SMA3Title_L0_8bpp.bin", (0x08165BE0,)),      # 082E3F50

    # Huffman graphics are included since they're reinserted as LZ77
    ("LZ77_MarioBros_layer.bin", (0x08111818,)),        # 082F9BF4
    ("LZ77_MarioBros_sprite.bin", (0x08111820,)),       # 082FDDB4
    ("LZ77_MarioBrosTitle_sprite.bin", (0x08110D9C, 0x08118710)), # 08304838
    ]

LZ77_tilemaps = [
    ("LZ77_YItitle_L3_W15.map8", (0x08199118,)),        # 0819DED0
    ("LZ77_YItitle_L3_W6.map8", (0x0819911C,)),         # 0819E5E8
    ("LZ77_YItitle_L1.map8", (0x080FE96C,)),            # 0819F0C8
    ("LZ77_WorldSelect_L1.map8", (0x08004740,)),        # 081FEBA8
    ("LZ77_WorldSelect_L2.map8", (0x08004748,)),        # 081FEECC
    ("LZ77_WorldSelect_L3.map8", (0x08004750,)),        # 081FF1D4
    ("LZ77_LevelSelect_Controls_Patient.map8", (0x08165678,)), # 08201AB8
    ("LZ77_LevelSelect_Controls_Hasty.map8", (0x0816567C,)),   # 08201D30
    ("LZ77_LevelSelect_L2_1.map8", (0x08164778,)),      # 08201F9C
    ("LZ77_LevelSelect_L2_2.map8", (0x0816477C,)),      # 08202468
    ("LZ77_LevelSelect_L2_3.map8", (0x08164780,)),      # 082029BC
    ("LZ77_LevelSelect_L2_4.map8", (0x08164784,)),      # 08202F80
    ("LZ77_LevelSelect_L2_5.map8", (0x08164788,)),      # 082034F0
    ("LZ77_LevelSelect_L2_6.map8", (0x0816478C,)),      # 08203A68
    ("LZ77_LevelSelect_L3_1.map8", (0x08164790,)),      # 08204020
    ("LZ77_LevelSelect_L3_2.map8", (0x08164794,)),      # 08204588
    ("LZ77_LevelSelect_L3_3.map8", (0x08164798,)),      # 08204B54
    ("LZ77_LevelSelect_L3_4.map8", (0x0816479C,)),      # 082051D4
    ("LZ77_LevelSelect_L3_5.map8", (0x081647A0,)),      # 0820580C
    ("LZ77_LevelSelect_L3_6.map8", (0x081647A4,)),      # 08205E9C
    ("LZ77_LevelSelect_LLBAR.map8", (0x08010EBC,)),     # 082066DC
    ("LZ77_ScoreCalc_L1.map8", (0x080E5C20,)),          # 082074E0
    ("LZ77_ScoreCalc_L3_8levels.map8", (0x080E490C,)),  # 082075F4
    ("LZ77_ScoreCalc_L3_10levels.map8", (0x080E48E4,)), # 082077B0
    ("LZ77_Gameplay_Kamek_L2.map8", (0x08017750,)),     # 08208D58
    ("LZ77_Gameplay_Kamek_L3.map8", (0x08017758,)),     # 082091A0
    ("LZ77_Gameplay_Raphael_L2.map8", (0x080145C8,)),   # 0820C1D4
    ("LZ77_Gameplay_Hookbill_L2.map8", (0x080CDBEC,)),  # 0820E054
    ("LZ77_100Cutscene_L1.map8", (0x080F7388,)),        # 08213AB0
    ("LZ77_100Cutscene_L2.map8", (0x080F739C,)),        # 0821400C
    ("LZ77_100Cutscene_L3.map8", (0x080F73B0,)),        # 08214A3C
    ("LZ77_100Cutscene_L0_2.map8", (0x080F8EA0,)),      # 08216FC4
    ("LZ77_100Cutscene_L0_1.map8", (0x080F7374,)),      # 0821724C
    ("LZ77_100Cutscene_L0_0.map8", (0x080F7E34,)),      # 082173D4
    ("LZ77_Gameplay_L2_11.map8", (                      # 08217518
        0x08167628, 0x08167640, 0x08167658)),           
    ("LZ77_Gameplay_L2_0E.map8", (0x0816761C,)),        # 0821783C
    ("LZ77_Gameplay_L2_1C.map8", (0x08167654,)),        # 08217AB0
    ("LZ77_Gameplay_L2_14.map8", (0x08167634,)),        # 08217D08
    ("LZ77_Gameplay_L2_1A.map8", (0x0816764C,)),        # 08218044
    ("LZ77_Gameplay_L2_08.map8", (0x08167604,)),        # 08218448
    ("LZ77_Gameplay_L2_06.map8", (0x081675FC,)),        # 08218964
    ("LZ77_Gameplay_L2_00.map8", (0x081675E4,)),        # 08218BD4
    ("LZ77_Gameplay_L2_04.map8", (0x081675F4,)),        # 08219490
    ("LZ77_Gameplay_L2_15.map8", (0x08167638,)),        # 08219808
    ("LZ77_Gameplay_L2_07.map8", (0x08167600,)),        # 08219B1C
    ("LZ77_Gameplay_L2_0B.map8", (0x08167610,)),        # 08219D80
    ("LZ77_Gameplay_L2_19.map8", (0x08167648,)),        # 0821A014
    ("LZ77_Gameplay_L2_01.map8", (0x081675E8,)),        # 0821A2C0
    ("LZ77_Gameplay_L2_0A.map8", (0x0816760C,)),        # 0821A63C
    ("LZ77_Gameplay_L2_02.map8", (0x081675EC,)),        # 0821A8BC
    ("LZ77_Gameplay_L2_09.map8", (0x08167608, 0x08167624)), # 0821ACD4
    ("LZ77_Gameplay_L2_1E.map8", (0x0816765C,)),        # 0821B020
    ("LZ77_Gameplay_L2_1B.map8", (0x08167650,)),        # 0821B2EC
    ("LZ77_Gameplay_L2_12.map8", (0x0816762C,)),        # 0821B4D8
    ("LZ77_Gameplay_L2_0F.map8", (0x08167620,)),        # 0821B734
    ("LZ77_Gameplay_L2_13.map8", (0x08167630,)),        # 0821B944
    ("LZ77_Gameplay_L2_0D.map8", (0x08167618,)),        # 0821BDBC
    ("LZ77_Gameplay_L2_03.map8", (0x081675F0,)),        # 0821C0CC
    ("LZ77_Gameplay_L2_05.map8", (0x081675F8,)),        # 0821C2D4
    ("LZ77_Gameplay_L2_0C.map8", (0x08167614,)),        # 0821C938
    ("LZ77_Gameplay_L2_1F.map8", (0x08167660,)),        # 0821CDA4
    ("LZ77_Gameplay_L2_16.map8", (0x0816763C,)),        # 0821D090
    ("LZ77_Gameplay_L2_18.map8", (0x08167644,)),        # 0821D49C
    ("LZ77_Gameplay_L3_1B.map8", (0x081676D8,)),        # 0821D9F0
    ("LZ77_Gameplay_L3_2B.map8", (0x08167718,)),        # 0821DB98
    ("LZ77_Gameplay_L3_02.map8", (                      # 0821DE64
        0x08167674, 0x08167680, 0x08167684, 0x08167688, 0x0816768C, 0x08167698)),
    ("LZ77_Gameplay_L3_00.map8", (0x0816766C, 0x08167690)), # 0821E3B0
    ("LZ77_Gameplay_L3_12.map8", (0x081676B4,)),        # 0821E4AC
    ("LZ77_Gameplay_L3_0D.map8", (0x081676A0,)),        # 0821E75C
    ("LZ77_Gameplay_L3_27.map8", (0x08167708,)),        # 0821EC5C
    ("LZ77_Gameplay_L3_28.map8", (0x0816770C,)),        # 0821EE88
    ("LZ77_Gameplay_L3_18.map8", (0x081676CC,)),        # 0821F0E4
    ("LZ77_Gameplay_L3_10.map8", (0x081676AC,)),        # 0821F288
    ("LZ77_Gameplay_L3_23.map8", (0x081676F8,)),        # 0821F42C
    ("LZ77_Gameplay_L3_14.map8", (0x081676BC,)),        # 0821F600
    ("LZ77_Gameplay_L3_20.map8", (0x081676EC,)),        # 0821F7B8
    ("LZ77_Gameplay_L3_29.map8", (0x08167710,)),        # 0821F970
    ("LZ77_Gameplay_L3_16.map8", (0x081676C4,)),        # 0821FB54
    ("LZ77_Gameplay_L3_13.map8", (0x081676B8, 0x081676E0)), # 0821FE10
    ("LZ77_Gameplay_L3_1C.map8", (0x081676DC,)),        # 0821FF10
    ("LZ77_Gameplay_L3_19.map8", (0x081676D0,)),        # 08220078
    ("LZ77_Gameplay_L3_2E.map8", (0x08167724,)),        # 0822017C
    ("LZ77_Gameplay_L3_2C.map8", (0x0816771C, 0x08167720)), # 08220328
    ("LZ77_Gameplay_L3_2A.map8", (0x08167714,)),        # 082204A0
    ("LZ77_Gameplay_L3_01.map8", (0x08167670,)),        # 08220694
    ("LZ77_Gameplay_L3_1A.map8", (0x081676D4,)),        # 08220798
    ("LZ77_Gameplay_L3_0C.map8", (0x0816769C,)),        # 082208DC
    ("LZ77_Gameplay_L3_15.map8", (0x081676C0,)),        # 08220AC8
    ("LZ77_Gameplay_L3_0A.map8", (0x08167694,)),        # 08220C20
    ("LZ77_Gameplay_L3_03.map8", (0x08167678, 0x0816767C)), # 08220D1C
    ("LZ77_Gameplay_L3_22.map8", (0x081676F4,)),        # 08220E2C
    ("LZ77_Gameplay_L3_0E.map8", (0x081676A4,)),        # 08220FA0
    ("LZ77_Gameplay_L3_25.map8", (0x08167700,)),        # 082212B4
    ("LZ77_Gameplay_L3_1E.map8", (0x081676E4,)),        # 082215C8
    ("LZ77_Gameplay_L3_1F.map8", (0x081676E8,)),        # 082217D0
    ("LZ77_Gameplay_L3_0F.map8", (0x081676A8,)),        # 082218D4
    ("LZ77_Gameplay_L3_11.map8", (0x081676B0,)),        # 08221B7C
    ("LZ77_Gameplay_L3_17.map8", (0x081676C8,)),        # 08221DB8
    ("LZ77_Gameplay_L3_21.map8", (0x081676F0,)),        # 08221F3C
    ("LZ77_Gameplay_L3_24.map8", (0x081676FC,)),        # 08222068
    ("LZ77_Gameplay_L3_26.map8", (0x08167704,)),        # 082222BC
    ("LZ77_Gameplay_L3_2F.map8", (0x08167728,)),        # 08222464
    ("LZ77_IntroCutscene_L2.map8", (0x080F60F4,)),      # 082225D4
    ("LZ77_IntroCutscene_L3.map8", (0x080F60FC,)),      # 08223004
    ("LZ77_BanditMinigame_L1.map8", (0x080EA78C,)),     # 082272CC
    ("LZ77_BanditMinigame_L2_BG.map8", (0x08195E48,)),  # 082278F0
    ("LZ77_BanditMinigame_L2_win.map8", (0x08195E4C,)), # 08227A18
    ("LZ77_BanditMinigame_L2_loss.map8", (0x08195E50,)), # 08227B54
    ("LZ77_GoalMinigame_L1_0.map8", (                   # 0824ACD0
        0x08196B18, 0x08196B20, 0x08196B24, 0x08196B28, 0x08196B2C)),
    ("LZ77_GoalMinigame_L1_2.map8", (0x08196B1C,)),     # 0824AE74
    ("LZ77_GoalMinigame_L2_1.map8", (0x08196B30,)),     # 0824B098
    ("LZ77_GoalMinigame_L2_2.map8", (0x08196B34,)),     # 0824B2D4
    ("LZ77_GoalMinigame_L2_4.map8", (0x08196B3C,)),     # 0824B504
    ("LZ77_GoalMinigame_L3.map8", (0x080EFD10,)),       # 0824B6B0
    ("LZ77_GoalMinigame_L2_3.map8", (0x08196B38,)),     # 0824B84C
    ("LZ77_GoalMinigame_L2_5.map8", (0x08196B40,)),     # 0824B9E0
    ("LZ77_GoalMinigame_L2_6.map8", (0x08196B44,)),     # 0824BC50
    ("LZ77_Gameplay_BossKeyhole.map8", (0x080BBCB4,)),  # 0824BFAC
    ("LZ77_StoryIntro_L2.map8", (0x08165B80,)),         # 082D5E5C
    ("LZ77_StoryIntro_L01_0.map8", (0x08165B68,)),      # 082D6078
    ("LZ77_StoryIntro_L01_1.map8", (0x08030CE8, 0x08165B74)), # 082D6444
    ("LZ77_StoryIntro_L01_2.map8", (0x08030BA0,)),      # 082D68C0
    ("LZ77_StoryIntro_L01_3.map8", (0x08030DCC,)),      # 082D6B68
    ("LZ77_StoryIntro_L01_4.map8", (0x08030EE0,)),      # 082D6D84
    ("LZ77_StoryIntro_L01_5.map8", (0x08030FD8,)),      # 082D6FE0
    ("LZ77_StoryIntro_L01_6.map8", (0x0803113C,)),      # 082D71C8
    ("LZ77_StoryIntro_L01_7.map8", (0x08031270,)),      # 082D7414
    ("LZ77_Credits_L0.map8", (0x08165BBC,)),            # 082DCD70
    ("LZ77_Credits_L1_0.map8", (0x08165BC8,)),          # 082DCF80
    ("LZ77_Credits_L1_1.map8", (0x0816DC04,)),          # 082DD134
    ("LZ77_Credits_L1_2.map8", (0x0816DC08,)),          # 082DD378
    ("LZ77_Credits_L1_3.map8", (0x0816DC0C,)),          # 082DD568
    ("LZ77_Credits_L1_4.map8", (0x0816DC10,)),          # 082DD788
    ("LZ77_Credits_L2.map8", (0x080343F0,)),            # 082DDA18
    ("LZ77_ChooseAGame_L0.map8", (0x0810D7C0,)),        # 082DFCB0
    ("LZ77_ChooseAGame_L1.map8", (0x0810D7C4,)),        # 082DFF44
    ("LZ77_ChooseAGame_L2.map8", (0x0810D7C8,)),        # 082E00D8
    ("LZ77_SMA3Title_L0.map8", (0x08165C04,)),          # 082E6FE0
    ("LZ77_SMA3Title_L1.map8", (0x08165C10,)),          # 082E72D0
    ("LZ77_SaveDataCorruption.map8", (0x080FA494,)),    # 082E8830
    ("LZ77_MarioBros_L3_0.map8", (0x08111920,)),        # 082ED724
    ("LZ77_MarioBros_L3_1.map8", (0x08111928,)),        # 082EDC60
    ("LZ77_MarioBros_L3_2.map8", (0x08111938,)),        # 082EE204
    ("LZ77_MarioBros_L3_3.map8", (0x08111C10,)),        # 082EE764
    ("LZ77_MarioBrosTitle_L2.map8", (                   # 082F11F8
        0x08110DB4, 0x08118DC8, 0x08119424)),
    ("LZ77_MarioBrosTitle_L1.map8", (                   # 082F1508
        0x08110DA4, 0x08118DB8, 0x08119414, 0x08119C04)),
    ("LZ77_MarioBrosTitle_L0.map8", (                   # 082F1640
        0x08110DBC, 0x08118DC0, 0x0811941C, 0x08119C0C)),
    ]

# Unreferenced LZ77 compressed data included in the ROM.
# Can be exported but not imported.
LZ77_unused = [
    ("LZ77_Unused0820649C.map8", 0x0820649C),
    ("LZ77_Unused08208918.map8", 0x08208918),
    ("LZ77_Unused0821C58C.map8", 0x0821C58C),
    ("LZ77_Unused0821EA54.map8", 0x0821EA54),
    ]

vanillacompressedregions = (
    (0x081EF954, 0x081F897C),
    (0x081FE17C, 0x082016B8),
    (0x08201AB8, 0x082068E0),
    (0x082074E0, 0x082095E4),
    (0x082097E4, 0x082135CC),
    (0x08213AB0, 0x082157C4),
    (0x08216FC4, 0x0822348C),
    (0x082255CC, 0x0824BE2C),
    (0x0824BFAC, 0x0827987C),
    (0x0828F87C, 0x0828FEA4),
    (0x082AAEA4, 0x082C7008),
    (0x082D5E5C, 0x082D75F8),
    (0x082D7FF8, 0x082DCD30),
    (0x082DCD70, 0x082DE31C),
    (0x082DEFBC, 0x082DFC50),
    (0x082DFCB0, 0x082E02CC),
    (0x082E02FC, 0x082E2E3C),
    (0x082E3EE4, 0x082E6E00),
    (0x082E6FE0, 0x082E7400),
    (0x082E7740, 0x082E8E84),
    (0x082F11F8, 0x082F1768),
    (0x082F99A8, 0x083077B0),
    )

# Uncompressed graphics export pointers.
# These should be split into individual files by purpose,
# once the purpose is documented.
uncompressed_graphics = [
    (0x081F897C, "Graphics_081F897C_LevelSelect_A06.bin", 0x1800),
    (0x081FA17C, "Graphics_081FA17C_LevelSelect_800.bin", 0x2000),
    (0x081FC17C, "Graphics_081FC17C_LevelSelect_A00.bin", 0x2000),
    (0x082068E0, "Graphics_082068E0.bin", 0xC00),
    (0x082157C4, "Graphics_082157C4.bin", 0x1800),
    (0x082235CC, "Graphics_082235CC.bin", 0x2000),
    (0x0827987C, "Graphics_0827987C.bin", 0x16000),
    (0x0828FEA4, "Graphics_0828FEA4.bin", 0x1A000),
    (0x082C7008, "Graphics_082C7008.bin", 0x8000),
    ]

textgraphics = {
        # graphics ptr, widths ptr, charlength, start
    "main":(0x082F63CC, 0x082F62CC, 0x100, 0),
    "credits":(0x0816D509, 0x0816D489, 0x80, 0x80),
    }
messageimages = 0x080E87A8      # 082F6FCC
