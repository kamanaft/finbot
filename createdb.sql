create table budget(
    codename varchar(255) primary key,
    daily_limit integer
);

create table category(
    codename varchar(255) primary key,
    name varchar(255),
    is_base_expense boolean,
    aliases text
);

create table expense(
    id integer primary key,
    amount integer,
    created datetime,
    category_codename integer,
    raw_text text,
    FOREIGN KEY(category_codename) REFERENCES category(codename)
);

insert into category (codename, name, is_base_expense, aliases)
values
    ("products", "potraviny", true, "jídlo"),
    ("coffee", "kava", true, ""),
    ("dinner", "oběd", true, "menza, hospoda, denní nabídka, kavárna"),
    ("cafe", "kavárna", true, "reataurace, MacDonald's, MacDonalds, Mekáč, kfc, KFC, BurgerKing"),
    ("transport", "doprava", false, "metro, autobus, tramvaj, mhd, MHD, socka"),
    ("taxi", "taxi", false, "bolt, uber, taxik, liftago"),
    ("phone", "mobil", false, "TMobile, Vodafone, O2, o2, Tmobile, vodafone"),
    ("books", "knihy", false, "literatura, lit"),
    ("internet", "internet", false, "inet, www"),
    ("subscriptions", "předplatné", false, "sub"),
    ("other", "jiné", true, "");

insert into budget(codename, daily_limit) values ('base', 500);
